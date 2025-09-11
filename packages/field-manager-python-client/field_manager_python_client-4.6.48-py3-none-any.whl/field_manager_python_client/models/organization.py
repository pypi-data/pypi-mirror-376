import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.role_enum import RoleEnum
from ..models.standard_type import StandardType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.role import Role


T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """
    Attributes:
        organization_id (UUID):
        name (str):
        number_of_projects (int):
        default_role (RoleEnum):
        external_id (Union[None, Unset, str]):
        short_name (Union[None, Unset, str]):
        email_domains (Union[None, Unset, str]):
        authentication_alias (Union[None, Unset, str]):
        authentication_issuer (Union[None, Unset, str]):
        created_at (Union[None, Unset, datetime.datetime]):
        updated_at (Union[None, Unset, datetime.datetime]):
        effective_role (Union['Role', None, Unset]):
        default_standard_id (Union[None, StandardType, Unset]):
        available_standard_ids (Union[Unset, list[StandardType]]):
    """

    organization_id: UUID
    name: str
    number_of_projects: int
    default_role: RoleEnum
    external_id: Union[None, Unset, str] = UNSET
    short_name: Union[None, Unset, str] = UNSET
    email_domains: Union[None, Unset, str] = UNSET
    authentication_alias: Union[None, Unset, str] = UNSET
    authentication_issuer: Union[None, Unset, str] = UNSET
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    updated_at: Union[None, Unset, datetime.datetime] = UNSET
    effective_role: Union["Role", None, Unset] = UNSET
    default_standard_id: Union[None, StandardType, Unset] = UNSET
    available_standard_ids: Union[Unset, list[StandardType]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.role import Role

        organization_id = str(self.organization_id)

        name = self.name

        number_of_projects = self.number_of_projects

        default_role = self.default_role.value

        external_id: Union[None, Unset, str]
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        short_name: Union[None, Unset, str]
        if isinstance(self.short_name, Unset):
            short_name = UNSET
        else:
            short_name = self.short_name

        email_domains: Union[None, Unset, str]
        if isinstance(self.email_domains, Unset):
            email_domains = UNSET
        else:
            email_domains = self.email_domains

        authentication_alias: Union[None, Unset, str]
        if isinstance(self.authentication_alias, Unset):
            authentication_alias = UNSET
        else:
            authentication_alias = self.authentication_alias

        authentication_issuer: Union[None, Unset, str]
        if isinstance(self.authentication_issuer, Unset):
            authentication_issuer = UNSET
        else:
            authentication_issuer = self.authentication_issuer

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        elif isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        effective_role: Union[None, Unset, dict[str, Any]]
        if isinstance(self.effective_role, Unset):
            effective_role = UNSET
        elif isinstance(self.effective_role, Role):
            effective_role = self.effective_role.to_dict()
        else:
            effective_role = self.effective_role

        default_standard_id: Union[None, Unset, str]
        if isinstance(self.default_standard_id, Unset):
            default_standard_id = UNSET
        elif isinstance(self.default_standard_id, StandardType):
            default_standard_id = self.default_standard_id.value
        else:
            default_standard_id = self.default_standard_id

        available_standard_ids: Union[Unset, list[str]] = UNSET
        if not isinstance(self.available_standard_ids, Unset):
            available_standard_ids = []
            for available_standard_ids_item_data in self.available_standard_ids:
                available_standard_ids_item = available_standard_ids_item_data.value
                available_standard_ids.append(available_standard_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "organization_id": organization_id,
                "name": name,
                "number_of_projects": number_of_projects,
                "default_role": default_role,
            }
        )
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if short_name is not UNSET:
            field_dict["short_name"] = short_name
        if email_domains is not UNSET:
            field_dict["email_domains"] = email_domains
        if authentication_alias is not UNSET:
            field_dict["authentication_alias"] = authentication_alias
        if authentication_issuer is not UNSET:
            field_dict["authentication_issuer"] = authentication_issuer
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if effective_role is not UNSET:
            field_dict["effective_role"] = effective_role
        if default_standard_id is not UNSET:
            field_dict["default_standard_id"] = default_standard_id
        if available_standard_ids is not UNSET:
            field_dict["available_standard_ids"] = available_standard_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.role import Role

        d = dict(src_dict)
        organization_id = UUID(d.pop("organization_id"))

        name = d.pop("name")

        number_of_projects = d.pop("number_of_projects")

        default_role = RoleEnum(d.pop("default_role"))

        def _parse_external_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        def _parse_short_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        short_name = _parse_short_name(d.pop("short_name", UNSET))

        def _parse_email_domains(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        email_domains = _parse_email_domains(d.pop("email_domains", UNSET))

        def _parse_authentication_alias(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        authentication_alias = _parse_authentication_alias(d.pop("authentication_alias", UNSET))

        def _parse_authentication_issuer(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        authentication_issuer = _parse_authentication_issuer(d.pop("authentication_issuer", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_effective_role(data: object) -> Union["Role", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                effective_role_type_0 = Role.from_dict(data)

                return effective_role_type_0
            except:  # noqa: E722
                pass
            return cast(Union["Role", None, Unset], data)

        effective_role = _parse_effective_role(d.pop("effective_role", UNSET))

        def _parse_default_standard_id(data: object) -> Union[None, StandardType, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                default_standard_id_type_0 = StandardType(data)

                return default_standard_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, StandardType, Unset], data)

        default_standard_id = _parse_default_standard_id(d.pop("default_standard_id", UNSET))

        available_standard_ids = []
        _available_standard_ids = d.pop("available_standard_ids", UNSET)
        for available_standard_ids_item_data in _available_standard_ids or []:
            available_standard_ids_item = StandardType(available_standard_ids_item_data)

            available_standard_ids.append(available_standard_ids_item)

        organization = cls(
            organization_id=organization_id,
            name=name,
            number_of_projects=number_of_projects,
            default_role=default_role,
            external_id=external_id,
            short_name=short_name,
            email_domains=email_domains,
            authentication_alias=authentication_alias,
            authentication_issuer=authentication_issuer,
            created_at=created_at,
            updated_at=updated_at,
            effective_role=effective_role,
            default_standard_id=default_standard_id,
            available_standard_ids=available_standard_ids,
        )

        organization.additional_properties = d
        return organization

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
