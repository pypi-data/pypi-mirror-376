from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="ExperimentDownloadDataSchemaTestsItemEvaluationsItem")


@_attrs_define
class ExperimentDownloadDataSchemaTestsItemEvaluationsItem:
    """
    Attributes:
        judge_prompt (str):
        judge_response (str):
        risk_triggered (bool):
        risk_type (str):
    """

    judge_prompt: str
    judge_response: str
    risk_triggered: bool
    risk_type: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        judge_prompt = self.judge_prompt

        judge_response = self.judge_response

        risk_triggered = self.risk_triggered

        risk_type = self.risk_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "judge_prompt": judge_prompt,
                "judge_response": judge_response,
                "risk_triggered": risk_triggered,
                "risk_type": risk_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        judge_prompt = d.pop("judge_prompt")

        judge_response = d.pop("judge_response")

        risk_triggered = d.pop("risk_triggered")

        risk_type = d.pop("risk_type")

        experiment_download_data_schema_tests_item_evaluations_item = cls(
            judge_prompt=judge_prompt,
            judge_response=judge_response,
            risk_triggered=risk_triggered,
            risk_type=risk_type,
        )

        experiment_download_data_schema_tests_item_evaluations_item.additional_properties = d
        return experiment_download_data_schema_tests_item_evaluations_item

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
