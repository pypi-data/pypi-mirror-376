from __future__ import annotations

import inspect
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

from django.conf import settings
from django.db import connection, models
from django.db import transaction as _transaction
from django.http import Http404, HttpRequest
from django.http.response import HttpResponseBase
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.inspectors import PaginatorInspector, ViewInspector
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import BasePagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from .inspectors import AutoSchema
from .request import ASRequest
from .response import StatusResponse
from .settings import api_settings

Serializer = type[serializers.BaseSerializer] | serializers.BaseSerializer
JsonValue = Mapping | Iterable | float | int | bool
ApiMethod = Callable[..., HttpResponseBase | JsonValue | None]
WrappedMethod = Callable[["ProcessEvent"], HttpResponseBase]
SwaggerResponse = openapi.Response | Serializer


@dataclass
class ProcessEvent:
    request: ASRequest
    view: Callable | None
    args: tuple
    kwargs: dict

    def get_object(self):
        return self.view.get_object() if self.detail else None  # type: ignore

    @property
    def query_data(self):
        return self.request.GET

    @property
    def body_data(self):
        return self.request.data

    @property
    def detail(self) -> bool:
        return self.view.detail if self.view else False


class HttpError(Exception):
    def __init__(self, content: dict | str | Any = "", status: int = status.HTTP_400_BAD_REQUEST):
        if isinstance(content, dict):
            self.content = content
        else:
            self.content = {"detail": content}
        self.status = status


def get_object_or_422(qs: type[models.Model] | models.QuerySet, *args, **kwargs) -> models.Model:
    """Get an object from a queryset or raise a 422 error if it doesn't exist."""
    model = qs.model if isinstance(qs, models.QuerySet) else qs
    try:
        if isinstance(qs, models.QuerySet):
            return qs.get(*args, **kwargs)
        return qs.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        raise HttpError(_("Not found."), status=status.HTTP_422_UNPROCESSABLE_ENTITY)


def check_exists(qs: type[models.Model] | models.QuerySet, *args, raise_error=True, **kwargs) -> bool:
    """Check if an object exists in a queryset or raise a 422 error if it doesn't exist."""
    model = qs.model if isinstance(qs, models.QuerySet) else qs
    flag = model.objects.filter(*args, **kwargs).exists()
    if raise_error and not flag:
        raise HttpError(_("Not found."), status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return flag


def is_accept_json(request: HttpRequest):
    """Check if the request accepts JSON."""
    return request.headers.get("accept", "").split(";")[0] == "application/json"


def apischema(
    *,
    permissions: Iterable[type[BasePermission]] | None = None,
    query: Serializer | None = None,
    body: Serializer | None = None,
    response: SwaggerResponse | StatusResponse | None = None,
    responses: dict[int, SwaggerResponse | Any] | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: Sequence[str] | None = None,
    extra_tags: Sequence[str] | None = None,
    transaction: bool | None = None,
    sqllogging: bool | None = None,
    sqllogging_callback: Callable[[Any], None] | None = None,
    deprecated: bool = False,
    pagination_class: type[BasePagination] | None = None,
    paginator_inspectors: Sequence[type[PaginatorInspector]] | None = None,
    auto_schema: type[ViewInspector] | None = None,
    **extra_kwargs: Any,
) -> Callable[[ApiMethod], Callable[..., HttpResponseBase]]:
    """
    Args:
        permissions (Iterable[type[BasePermission]] | None, optional): The permissions needed to access the endpoint.
        query (Serializer | None, optional): The serializer used for query parameters.
        body (Serializer | None, optional): The serializer used for the request body.
        response (SwaggerResponse | StatusResponse | None, optional): The OpenAPI schema for the response.
        responses (dict[int, SwaggerResponse] | None, optional): The OpenAPI schemas for various response codes.
        summary (str | None, optional): A brief summary of the endpoint.
        description (str | None, optional): A detailed description of the endpoint.
        tags (Sequence[str] | None, optional): The tags associated with the endpoint.
        extra_tags (Sequence[str] | None, optional): Additional tags for the endpoint.
        transaction (bool, optional): Indicates if the method should be wrapped in a transaction.
        sqllogging (bool, optional): Indicates if SQL queries should be logged.
        sqllogging_callback (Callable[[Any], None] | None, optional): A callback function for SQL queries.
        deprecated (bool, optional): Indicates if the endpoint is deprecated.
        pagination_class (type[BasePagination] | None, optional): The pagination class for the endpoint.
        paginator_inspectors (Sequence[type[PaginatorInspector]] | None, optional): The paginator inspectors for the endpoint.
        auto_schema (type[ViewInspector] | None, optional): The AutoSchema class for the endpoint.
        **extra_kwargs (Any): Additional keyword arguments for the swagger_auto_schema.

    Returns:
        Callable[[ApiMethod], Callable[..., HttpResponseBase]]: The method after decoration.
    """

    def decorator(method: ApiMethod) -> Callable[..., HttpResponseBase]:
        wrapper = _response_processor(method)
        if query or body:
            wrapper = _serializer_processor(wrapper, query, body)
        if api_settings.transaction(transaction):
            wrapper = _transaction.atomic(wrapper)
        if api_settings.sqllogging(sqllogging) and settings.DEBUG:
            wrapper = _sql_logger(wrapper, sqllogging_callback)
        if permissions:
            wrapper = _permission_processor(wrapper, permissions)
        wrapper = _excpetion_catcher(wrapper)
        wrapper = swagger_schema(
            method=method,
            permissions=permissions,
            query=query,
            body=body,
            response=response,
            responses=responses,
            summary=summary,
            description=description,
            tags=tags,
            extra_tags=extra_tags,
            deprecated=deprecated,
            pagination_class=pagination_class,
            paginator_inspectors=paginator_inspectors,
            auto_schema=auto_schema,
            **extra_kwargs,
        )(wrapper)
        return wrapper

    return decorator


def _sql_logger(method: WrappedMethod, callback: Callable[[Any], None] | None = None):
    def wrapper(event: ProcessEvent):
        import sqlparse
        from rich import print as rprint
        from rich.padding import Padding

        response = method(event)
        cache = []
        for query in connection.queries:
            if callback is not None:
                callback(query)
            sql = sqlparse.format(query["sql"], reindent=api_settings.sqllogging_reindent()).strip()
            cache.append(f"[SQL] Time: {query['time']}")
            cache.append(Padding(sql, (0, 0, 0, 2)))
        rprint(*cache)
        return response

    wrapper.__name__ = method.__name__
    return wrapper


def _excpetion_catcher(method: WrappedMethod):
    def exception_handler(event: ProcessEvent):
        try:
            response = method(event)
        except Http404 as exc:
            raise exc
        except HttpError as exc:
            return Response(exc.content, status=exc.status)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as exc:
            traceback.print_exception(exc)
            if is_accept_json(event.request):
                return Response({"detail": _("Server error.")}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            raise exc
        return response

    def default_handler(*args, **kwds):
        if hasattr(args[0], "request"):
            request, view = args[1], args[0]
        else:
            request, view = args[0], None
        event = ProcessEvent(request=request, view=view, args=args, kwargs=kwds)
        return exception_handler(event)

    default_handler.__name__ = method.__name__
    return default_handler


def _response_processor(method: ApiMethod):
    def wrapper(event: ProcessEvent) -> HttpResponseBase:
        response = method(*event.args, **event.kwargs)
        if response is None:
            response = Response(status=status.HTTP_204_NO_CONTENT)
        elif isinstance(response, HttpResponseBase):
            response = response
        else:
            response = Response(response)
        return response

    wrapper.__name__ = method.__name__
    return wrapper


def _serializer_processor(
    method: WrappedMethod,
    query: Serializer | None = None,
    body: Serializer | None = None,
):
    if query:

        def get_serializer(event: ProcessEvent):
            if isinstance(query, serializers.BaseSerializer):
                serializer = query
                serializer.instance = event.get_object()
                serializer.initial_data = event.query_data
            else:
                serializer = query(instance=event.get_object(), data=event.query_data)
            return serializer

    elif body:

        def get_serializer(event: ProcessEvent):
            if isinstance(body, serializers.BaseSerializer):
                serializer = body
                serializer.instance = event.get_object()
                serializer.initial_data = event.body_data
            else:
                serializer = body(instance=event.get_object(), data=event.body_data)
            return serializer

    else:
        raise ValueError("query or body is required")

    def wrapper(event: ProcessEvent):
        serializer = get_serializer(event)
        serializer.is_valid(raise_exception=True)

        event.request.serializer = serializer
        event.request.validated_data = serializer.validated_data
        return method(event)

    wrapper.__name__ = method.__name__
    return wrapper


def _permission_processor(
    method: WrappedMethod,
    permissions: Iterable[type[BasePermission]],
):
    __permissions = [permission() for permission in permissions]

    def wrapper(event: ProcessEvent):
        for permission in __permissions:
            if permission.has_permission(event.request, event.view):  # type: ignore
                return method(event)
        raise HttpError(_("You do not have permission to perform this action."), status=status.HTTP_403_FORBIDDEN)

    wrapper.__name__ = method.__name__
    return wrapper


class Response422Serializer(serializers.Serializer):
    detail = serializers.Field()


def swagger_schema(
    method: ApiMethod,
    permissions: Iterable[type[BasePermission]] | None = None,
    query: Serializer | None = None,
    body: Serializer | None = None,
    response: SwaggerResponse | StatusResponse | None = None,
    responses: dict[int, SwaggerResponse] | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: Sequence[str] | None = None,
    extra_tags: Sequence[str] | None = None,
    deprecated: bool | None = None,
    pagination_class: type[BasePagination] | None = None,
    paginator_inspectors: Sequence[type[PaginatorInspector]] | None = None,
    security: list[dict[str, list[str]]] | None = None,
    auto_schema: type[ViewInspector] | None = None,
    **extra_kwargs: Any,
):
    if response is not None and inspect.isclass(response):
        response = response()

    responses = responses or {}
    if response is not None:
        if isinstance(response, StatusResponse):
            responses.setdefault(response.status_code, response.response)
        else:
            responses.setdefault(status.HTTP_200_OK, response)
    if query or body:
        responses.setdefault(status.HTTP_422_UNPROCESSABLE_ENTITY, Response422Serializer())
    responses = dict(sorted(responses.items(), key=lambda x: x[0]))

    if method.__doc__ is None:
        _summary = None
    else:
        _summary, *docs = method.__doc__.strip("\n").splitlines()
        if description is None:
            if sys.version_info >= (3, 13):
                if docs:
                    indent_length = min((len(i) - len(i.lstrip(" ")) for i in docs))
                    docs = [i[indent_length:] for i in docs]
            description = "\n".join(docs).strip("\n")
    if summary is None:
        summary = _summary

    return swagger_auto_schema(
        permissions=permissions,
        query_serializer=query,
        request_body=body,
        responses=responses,
        operation_summary=summary,
        operation_description=description,
        tags=tags,
        extra_tags=extra_tags,
        deprecated=deprecated,
        pagination_class=pagination_class,
        paginator_inspectors=paginator_inspectors,
        security=security,
        **{"auto_schema": AutoSchema} if api_settings.override_swagger_auto_schema(auto_schema) else {},  # type: ignore
        **extra_kwargs,
    )
