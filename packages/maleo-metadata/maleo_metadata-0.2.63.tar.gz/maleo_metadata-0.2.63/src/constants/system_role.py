from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.system_role import (
    BaseSystemRoleData,
    BasicSystemRoleData,
    StandardSystemRoleData,
    FullSystemRoleData,
)
from ..enums.system_role import Granularity, IdentifierType
from ..types.system_role import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseSystemRoleData]] = {
    Granularity.BASIC: BasicSystemRoleData,
    Granularity.STANDARD: StandardSystemRoleData,
    Granularity.FULL: FullSystemRoleData,
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
        ResourceIdentifier(key="system_roles", name="System Roles", slug="system-roles")
    ],
    details=None,
)
