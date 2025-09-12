from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.gender import (
    BaseGenderData,
    BasicGenderData,
    StandardGenderData,
    FullGenderData,
)
from ..enums.gender import Granularity, IdentifierType
from ..types.gender import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseGenderData]] = {
    Granularity.BASIC: BasicGenderData,
    Granularity.STANDARD: StandardGenderData,
    Granularity.FULL: FullGenderData,
}


IDENTIFIER_TYPE_VALUE_TYPE_MAP: Dict[
    IdentifierType, Callable[..., IdentifierValueType]
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="genders", name="Genders", slug="genders")],
    details=None,
)
