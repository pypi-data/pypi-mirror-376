from maleo.mixins.parameter import (
    OptionalListOfIds,
    OptionalListOfUuids,
    OptionalListOfKeys,
    OptionalListOfNames,
)
from maleo.schemas.request import (
    ReadSingleQuery as BaseReadSingleQuery,
    ReadPaginatedMultipleQuery,
)
from ..mixins.service import Granularity


class CommonQuery(Granularity):
    pass


class ReadSingleQuery(CommonQuery, BaseReadSingleQuery):
    pass


class ReadMultipleQuery(
    CommonQuery,
    ReadPaginatedMultipleQuery,
    OptionalListOfNames,
    OptionalListOfKeys,
    OptionalListOfUuids,
    OptionalListOfIds,
):
    pass
