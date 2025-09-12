from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.service import (
    BaseServiceData,
    BasicServiceData,
    StandardServiceData,
    FullServiceData,
)
from ..enums.service import Granularity, IdentifierType
from ..types.service import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseServiceData]] = {
    Granularity.BASIC: BasicServiceData,
    Granularity.STANDARD: StandardServiceData,
    Granularity.FULL: FullServiceData,
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
    identifiers=[ResourceIdentifier(key="services", name="Services", slug="services")],
    details=None,
)
