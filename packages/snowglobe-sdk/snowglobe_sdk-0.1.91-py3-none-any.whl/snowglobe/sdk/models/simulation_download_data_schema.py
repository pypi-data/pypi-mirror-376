from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.simulation_download_data_schema_tests_item import (
        SimulationDownloadDataSchemaTestsItem,
    )


T = TypeVar("T", bound="SimulationDownloadDataSchema")


@_attrs_define
class SimulationDownloadDataSchema:
    """
    Attributes:
        tests (list['SimulationDownloadDataSchemaTestsItem']):
    """

    tests: list["SimulationDownloadDataSchemaTestsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tests = []
        for tests_item_data in self.tests:
            tests_item = tests_item_data.to_dict()
            tests.append(tests_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tests": tests,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.simulation_download_data_schema_tests_item import (
            SimulationDownloadDataSchemaTestsItem,
        )

        d = dict(src_dict)
        tests = []
        _tests = d.pop("tests")
        for tests_item_data in _tests:
            tests_item = SimulationDownloadDataSchemaTestsItem.from_dict(
                tests_item_data
            )

            tests.append(tests_item)

        simulation_download_data_schema = cls(
            tests=tests,
        )

        simulation_download_data_schema.additional_properties = d
        return simulation_download_data_schema

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
