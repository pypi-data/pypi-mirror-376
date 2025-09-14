from maleo.mixins.general import IsRoot, IsParent, IsChild, IsLeaf
from maleo.mixins.parameter import (
    OptionalListOfIds,
    OptionalListOfUuids,
    OptionalListOfCodes,
    OptionalListOfParentIds,
    OptionalListOfKeys,
    OptionalListOfNames,
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
    OptionalListOfNames,
    OptionalListOfKeys,
    OptionalListOfCodes,
    OptionalListOfUuids,
    OptionalListOfIds,
):
    pass


class ReadMultipleQuery(
    CommonQuery,
    ReadPaginatedMultipleQuery,
    OptionalListOfNames,
    OptionalListOfKeys,
    OptionalListOfCodes,
    IsLeaf,
    IsChild,
    IsParent,
    IsRoot,
    OptionalListOfParentIds,
    OptionalListOfUuids,
    OptionalListOfIds,
):
    pass
