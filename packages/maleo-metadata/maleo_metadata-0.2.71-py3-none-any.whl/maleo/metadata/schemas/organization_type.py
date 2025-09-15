from maleo.mixins.parameter import (
    OptionalIds,
    OptionalUUIDs,
    OptionalKeys,
    OptionalNames,
)
from maleo.schemas.request import (
    ReadSingleQuery as BaseReadSingleQuery,
    ReadPaginatedMultipleQuery,
)
from ..mixins.organization_type import Granularity


class CommonQuery(Granularity):
    pass


class ReadSingleQuery(CommonQuery, BaseReadSingleQuery):
    pass


class ReadMultipleQuery(
    CommonQuery,
    ReadPaginatedMultipleQuery,
    OptionalNames,
    OptionalKeys,
    OptionalUUIDs,
    OptionalIds,
):
    pass
