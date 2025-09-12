from typing import Callable, Dict, Type
from uuid import UUID
from maleo.dtos.resource import Resource, ResourceIdentifier
from ..dtos.medical_role import (
    BaseMedicalRoleData,
    BasicMedicalRoleData,
    StandardMedicalRoleData,
    FullMedicalRoleData,
)
from ..enums.medical_role import Granularity, IdentifierType
from ..types.medical_role import IdentifierValueType


GRANULARITY_MODEL: Dict[Granularity, Type[BaseMedicalRoleData]] = {
    Granularity.BASIC: BasicMedicalRoleData,
    Granularity.STANDARD: StandardMedicalRoleData,
    Granularity.FULL: FullMedicalRoleData,
}


IDENTIFIER_TYPE_VALUE_TYPE_MAP: Dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
    IdentifierType.CODE: str,
    IdentifierType.KEY: str,
    IdentifierType.NAME: str,
}


RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(
            key="medical_roles", name="Medical Roles", slug="medical-roles"
        )
    ],
    details=None,
)
