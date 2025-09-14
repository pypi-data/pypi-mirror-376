import json
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from splitter_mr.schema import ReaderOutput
from splitter_mr.splitter import RecursiveJSONSplitter

# Helpers


@pytest.fixture
def reader_output():
    data = {"foo": {"bar": [1, 2, 3]}, "baz": "qux"}
    return ReaderOutput(
        text=json.dumps(data),
        document_name="sample.json",
        document_path="/tmp/sample.json",
        document_id="123",
        conversion_method="json",
        ocr_method=None,
    )


# Test cases


def test_recursive_json_splitter_instantiates_and_calls_splitter(reader_output):
    with patch(
        "splitter_mr.splitter.splitters.json_splitter.RecursiveJsonSplitter"
    ) as MockSplitter:
        mock_splitter = MockSplitter.return_value
        mock_splitter.split_text.return_value = [
            '{"foo": {"bar": [1, 2]}}',
            '{"foo": {"bar": [3]}, "baz": "qux"}',
        ]
        splitter = RecursiveJSONSplitter(chunk_size=100, min_chunk_size=10)
        result = splitter.split(reader_output)

        MockSplitter.assert_called_once_with(max_chunk_size=100, min_chunk_size=90)
        mock_splitter.split_text.assert_called_once_with(
            json_data=json.loads(reader_output.text), convert_lists=True
        )

        # Check output structure and values
        assert hasattr(result, "chunks")
        assert result.chunks == [
            '{"foo": {"bar": [1, 2]}}',
            '{"foo": {"bar": [3]}, "baz": "qux"}',
        ]
        assert hasattr(result, "split_method")
        assert result.split_method == "recursive_json_splitter"
        assert result.split_params["max_chunk_size"] == 100
        assert result.split_params["min_chunk_size"] == 10
        for field in [
            "chunks",
            "chunk_id",
            "document_name",
            "document_path",
            "document_id",
            "conversion_method",
            "ocr_method",
            "split_method",
            "split_params",
            "metadata",
        ]:
            assert hasattr(result, field)


def test_empty_text():
    with patch(
        "splitter_mr.splitter.splitters.json_splitter.RecursiveJsonSplitter"
    ) as MockSplitter:
        mock_splitter = MockSplitter.return_value
        mock_splitter.split_json.return_value = []
        splitter = RecursiveJSONSplitter(chunk_size=100, min_chunk_size=10)
        reader_output = ReaderOutput(text=json.dumps({}))
        with pytest.raises(ValidationError):
            splitter.split(reader_output)
