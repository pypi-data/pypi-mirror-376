from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.organization_type import (
    BaseOrganizationTypeData,
    BasicOrganizationTypeData,
    StandardOrganizationTypeData,
    FullOrganizationTypeData,
)
from ..enums.organization_type import Granularity, IdentifierType
from ..types.organization_type import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseOrganizationTypeData]] = {
    Granularity.BASIC: BasicOrganizationTypeData,
    Granularity.STANDARD: StandardOrganizationTypeData,
    Granularity.FULL: FullOrganizationTypeData,
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
        ResourceIdentifier(
            key="organization_types",
            name="Organization Types",
            slug="organization-types",
        )
    ],
    details=None,
)
