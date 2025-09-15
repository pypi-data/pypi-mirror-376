from maleo.mixins.parameter import (
    Filters,
    DataStatuses,
    Sorts,
    Search,
    UseCache,
    StatusUpdateAction,
)
from maleo.dtos.pagination import BaseFlexiblePagination, BaseStrictPagination


class ReadSingleQuery(
    DataStatuses,
    UseCache,
):
    pass


class BaseReadMultipleQuery(
    Sorts,
    Search,
    DataStatuses,
    Filters,
    UseCache,
):
    pass


class ReadUnpaginatedMultipleQuery(
    BaseFlexiblePagination,
    BaseReadMultipleQuery,
):
    pass


class ReadPaginatedMultipleQuery(
    BaseStrictPagination,
    BaseReadMultipleQuery,
):
    pass


class StatusUpdateBody(StatusUpdateAction):
    pass
