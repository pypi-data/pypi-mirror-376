from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


from typing import cast

if TYPE_CHECKING:
    from ..models.experiment_download_data_schema_tests_item_evaluations_item import (
        ExperimentDownloadDataSchemaTestsItemEvaluationsItem,
    )


T = TypeVar("T", bound="ExperimentDownloadDataSchemaTestsItem")


@_attrs_define
class ExperimentDownloadDataSchemaTestsItem:
    """
    Attributes:
        id (str):
        prompt (str):
        response (str):
        tactics (list[str]):
        persona (str):
        topic (str):
        risk_type (str):
        evaluations (list['ExperimentDownloadDataSchemaTestsItemEvaluationsItem']):
    """

    id: str
    prompt: str
    response: str
    tactics: list[str]
    persona: str
    topic: str
    risk_type: str
    evaluations: list["ExperimentDownloadDataSchemaTestsItemEvaluationsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        prompt = self.prompt

        response = self.response

        tactics = self.tactics

        persona = self.persona

        topic = self.topic

        risk_type = self.risk_type

        evaluations = []
        for evaluations_item_data in self.evaluations:
            evaluations_item = evaluations_item_data.to_dict()
            evaluations.append(evaluations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "prompt": prompt,
                "response": response,
                "tactics": tactics,
                "persona": persona,
                "topic": topic,
                "riskType": risk_type,
                "evaluations": evaluations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_download_data_schema_tests_item_evaluations_item import (
            ExperimentDownloadDataSchemaTestsItemEvaluationsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        prompt = d.pop("prompt")

        response = d.pop("response")

        tactics = cast(list[str], d.pop("tactics"))

        persona = d.pop("persona")

        topic = d.pop("topic")

        risk_type = d.pop("riskType")

        evaluations = []
        _evaluations = d.pop("evaluations")
        for evaluations_item_data in _evaluations:
            evaluations_item = (
                ExperimentDownloadDataSchemaTestsItemEvaluationsItem.from_dict(
                    evaluations_item_data
                )
            )

            evaluations.append(evaluations_item)

        experiment_download_data_schema_tests_item = cls(
            id=id,
            prompt=prompt,
            response=response,
            tactics=tactics,
            persona=persona,
            topic=topic,
            risk_type=risk_type,
            evaluations=evaluations,
        )

        experiment_download_data_schema_tests_item.additional_properties = d
        return experiment_download_data_schema_tests_item

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
