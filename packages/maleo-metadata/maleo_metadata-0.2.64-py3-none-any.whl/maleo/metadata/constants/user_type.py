from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.user_type import (
    BaseUserTypeData,
    BasicUserTypeData,
    StandardUserTypeData,
    FullUserTypeData,
)
from ..enums.user_type import Granularity, IdentifierType
from ..types.user_type import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseUserTypeData]] = {
    Granularity.BASIC: BasicUserTypeData,
    Granularity.STANDARD: StandardUserTypeData,
    Granularity.FULL: FullUserTypeData,
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
        ResourceIdentifier(key="user_types", name="User Types", slug="user-types")
    ],
    details=None,
)
