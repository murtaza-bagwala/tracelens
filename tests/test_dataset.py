import pytest

from tracelens.models.dataset import Dataset, DatasetRow


def test_dataset_from_dict_round_trips_rows(insurance_faq_dataset_dict):
    dataset = Dataset.from_dict(insurance_faq_dataset_dict)

    assert dataset.name == "insurance_faq"
    assert len(dataset.rows) == len(insurance_faq_dataset_dict["rows"])
    assert dataset.rows[0].id == insurance_faq_dataset_dict["rows"][0]["id"]
    assert dataset.rows[0].reference == insurance_faq_dataset_dict["rows"][0]["reference"]


def test_dataset_row_defaults_context_and_metadata():
    row = DatasetRow.from_dict({"id": "a", "input": "q", "reference": "r"})

    assert row.context == ""
    assert row.metadata == {}


def test_dataset_row_missing_required_field_raises():
    with pytest.raises(ValueError):
        DatasetRow.from_dict({"id": "a", "input": "q"})


def test_dataset_missing_rows_raises():
    with pytest.raises(ValueError):
        Dataset.from_dict({"name": "empty"})
