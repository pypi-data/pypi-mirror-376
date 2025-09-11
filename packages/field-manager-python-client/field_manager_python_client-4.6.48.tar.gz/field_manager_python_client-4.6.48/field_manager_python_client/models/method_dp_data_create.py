import datetime
from collections.abc import Mapping
from typing import Any, Literal, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="MethodDPDataCreate")


@_attrs_define
class MethodDPDataCreate:
    """
    Attributes:
        depth (Union[float, str]): Depth (m). SGF code D.
        method_data_id (Union[None, UUID, Unset]):
        method_id (Union[None, UUID, Unset]):
        method_type_id (Union[Literal[25], Unset]):  Default: 25.
        created_at (Union[None, Unset, datetime.datetime]):
        updated_at (Union[None, Unset, datetime.datetime]):
        comment_code (Union[None, Unset, int]): Comment code. Two digit value.
        remarks (Union[None, Unset, str]):
        penetration_force (Union[None, Unset, float, str]): Penetration force (kN). SGF code A.
        penetration_rate (Union[None, Unset, float, str]): Penetration rate (mm/s). SGF code B.
        torque (Union[None, Unset, float, str]): Torque (kNm). SGF code V.
        ramming (Union[None, Unset, float, str]): Ramming (blow/0.2m)
        rotation_rate (Union[None, Unset, float, str]): Rotation rate (rpm). SGF code R.
        increased_rotation_rate (Union[None, Unset, bool]): rotation
    """

    depth: Union[float, str]
    method_data_id: Union[None, UUID, Unset] = UNSET
    method_id: Union[None, UUID, Unset] = UNSET
    method_type_id: Union[Literal[25], Unset] = 25
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    updated_at: Union[None, Unset, datetime.datetime] = UNSET
    comment_code: Union[None, Unset, int] = UNSET
    remarks: Union[None, Unset, str] = UNSET
    penetration_force: Union[None, Unset, float, str] = UNSET
    penetration_rate: Union[None, Unset, float, str] = UNSET
    torque: Union[None, Unset, float, str] = UNSET
    ramming: Union[None, Unset, float, str] = UNSET
    rotation_rate: Union[None, Unset, float, str] = UNSET
    increased_rotation_rate: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        depth: Union[float, str]
        depth = self.depth

        method_data_id: Union[None, Unset, str]
        if isinstance(self.method_data_id, Unset):
            method_data_id = UNSET
        elif isinstance(self.method_data_id, UUID):
            method_data_id = str(self.method_data_id)
        else:
            method_data_id = self.method_data_id

        method_id: Union[None, Unset, str]
        if isinstance(self.method_id, Unset):
            method_id = UNSET
        elif isinstance(self.method_id, UUID):
            method_id = str(self.method_id)
        else:
            method_id = self.method_id

        method_type_id = self.method_type_id

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

        comment_code: Union[None, Unset, int]
        if isinstance(self.comment_code, Unset):
            comment_code = UNSET
        else:
            comment_code = self.comment_code

        remarks: Union[None, Unset, str]
        if isinstance(self.remarks, Unset):
            remarks = UNSET
        else:
            remarks = self.remarks

        penetration_force: Union[None, Unset, float, str]
        if isinstance(self.penetration_force, Unset):
            penetration_force = UNSET
        else:
            penetration_force = self.penetration_force

        penetration_rate: Union[None, Unset, float, str]
        if isinstance(self.penetration_rate, Unset):
            penetration_rate = UNSET
        else:
            penetration_rate = self.penetration_rate

        torque: Union[None, Unset, float, str]
        if isinstance(self.torque, Unset):
            torque = UNSET
        else:
            torque = self.torque

        ramming: Union[None, Unset, float, str]
        if isinstance(self.ramming, Unset):
            ramming = UNSET
        else:
            ramming = self.ramming

        rotation_rate: Union[None, Unset, float, str]
        if isinstance(self.rotation_rate, Unset):
            rotation_rate = UNSET
        else:
            rotation_rate = self.rotation_rate

        increased_rotation_rate: Union[None, Unset, bool]
        if isinstance(self.increased_rotation_rate, Unset):
            increased_rotation_rate = UNSET
        else:
            increased_rotation_rate = self.increased_rotation_rate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "depth": depth,
            }
        )
        if method_data_id is not UNSET:
            field_dict["method_data_id"] = method_data_id
        if method_id is not UNSET:
            field_dict["method_id"] = method_id
        if method_type_id is not UNSET:
            field_dict["method_type_id"] = method_type_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if comment_code is not UNSET:
            field_dict["comment_code"] = comment_code
        if remarks is not UNSET:
            field_dict["remarks"] = remarks
        if penetration_force is not UNSET:
            field_dict["penetration_force"] = penetration_force
        if penetration_rate is not UNSET:
            field_dict["penetration_rate"] = penetration_rate
        if torque is not UNSET:
            field_dict["torque"] = torque
        if ramming is not UNSET:
            field_dict["ramming"] = ramming
        if rotation_rate is not UNSET:
            field_dict["rotation_rate"] = rotation_rate
        if increased_rotation_rate is not UNSET:
            field_dict["increased_rotation_rate"] = increased_rotation_rate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_depth(data: object) -> Union[float, str]:
            return cast(Union[float, str], data)

        depth = _parse_depth(d.pop("depth"))

        def _parse_method_data_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                method_data_id_type_0 = UUID(data)

                return method_data_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        method_data_id = _parse_method_data_id(d.pop("method_data_id", UNSET))

        def _parse_method_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                method_id_type_0 = UUID(data)

                return method_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        method_id = _parse_method_id(d.pop("method_id", UNSET))

        method_type_id = cast(Union[Literal[25], Unset], d.pop("method_type_id", UNSET))
        if method_type_id != 25 and not isinstance(method_type_id, Unset):
            raise ValueError(f"method_type_id must match const 25, got '{method_type_id}'")

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

        def _parse_comment_code(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        comment_code = _parse_comment_code(d.pop("comment_code", UNSET))

        def _parse_remarks(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        remarks = _parse_remarks(d.pop("remarks", UNSET))

        def _parse_penetration_force(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        penetration_force = _parse_penetration_force(d.pop("penetration_force", UNSET))

        def _parse_penetration_rate(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        penetration_rate = _parse_penetration_rate(d.pop("penetration_rate", UNSET))

        def _parse_torque(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        torque = _parse_torque(d.pop("torque", UNSET))

        def _parse_ramming(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        ramming = _parse_ramming(d.pop("ramming", UNSET))

        def _parse_rotation_rate(data: object) -> Union[None, Unset, float, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float, str], data)

        rotation_rate = _parse_rotation_rate(d.pop("rotation_rate", UNSET))

        def _parse_increased_rotation_rate(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        increased_rotation_rate = _parse_increased_rotation_rate(d.pop("increased_rotation_rate", UNSET))

        method_dp_data_create = cls(
            depth=depth,
            method_data_id=method_data_id,
            method_id=method_id,
            method_type_id=method_type_id,
            created_at=created_at,
            updated_at=updated_at,
            comment_code=comment_code,
            remarks=remarks,
            penetration_force=penetration_force,
            penetration_rate=penetration_rate,
            torque=torque,
            ramming=ramming,
            rotation_rate=rotation_rate,
            increased_rotation_rate=increased_rotation_rate,
        )

        method_dp_data_create.additional_properties = d
        return method_dp_data_create

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
