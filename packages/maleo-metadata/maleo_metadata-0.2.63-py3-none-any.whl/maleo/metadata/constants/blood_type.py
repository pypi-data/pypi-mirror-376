from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.blood_type import (
    BaseBloodTypeData,
    BasicBloodTypeData,
    StandardBloodTypeData,
    FullBloodTypeData,
)
from ..enums.blood_type import Granularity, IdentifierType
from ..types.blood_type import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseBloodTypeData]] = {
    Granularity.BASIC: BasicBloodTypeData,
    Granularity.STANDARD: StandardBloodTypeData,
    Granularity.FULL: FullBloodTypeData,
}


IDENTIFIER_TYPE_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="blood_types", name="Blood Types", slug="blood-types")
    ],
    details=None,
)
