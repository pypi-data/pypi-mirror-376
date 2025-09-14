from maleo.mixins.general import IsRoot, IsParent, IsChild, IsLeaf
from maleo.mixins.parameter import (
    OptionalIds,
    OptionalUUIDs,
    OptionalCodes,
    OptionalParentIds,
    OptionalKeys,
    OptionalNames,
)
from maleo.schemas.request import (
    ReadSingleQuery as BaseReadSingleQuery,
    ReadPaginatedMultipleQuery,
)
from ..mixins.medical_role import Granularity


class CommonQuery(Granularity):
    pass


class ReadSingleQuery(CommonQuery, BaseReadSingleQuery):
    pass


class ReadMultipleSpecializationsQuery(
    CommonQuery,
    ReadPaginatedMultipleQuery,
    OptionalNames,
    OptionalKeys,
    OptionalCodes,
    OptionalUUIDs,
    OptionalIds,
):
    pass


class ReadMultipleQuery(
    CommonQuery,
    ReadPaginatedMultipleQuery,
    OptionalNames,
    OptionalKeys,
    OptionalCodes,
    IsLeaf,
    IsChild,
    IsParent,
    IsRoot,
    OptionalParentIds,
    OptionalUUIDs,
    OptionalIds,
):
    pass
