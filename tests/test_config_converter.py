import pytest
from unittest.mock import patch, Mock
import os
from os.path import join
from copy import deepcopy

from vitessce import (CellBrowserToVitessceConfigConverter, convert)
from vitessce.data_utils import (
    VAR_CHUNK_SIZE
)

valid_cellbrowser_config = {
    "fileVersions": {
        "inMatrix": {
            "fname": "/hive/data/inside/cells/datasets/adultPancreas/exprMatrix.csv.gz",
            "md5": "8da7a759a8",
            "size": 23363664,
            "mtime": "2018-10-16 23:29:40"
        },
        "outMatrix": {
            "fname": "/usr/local/apache/htdocs-cells/adultPancreas/exprMatrix.tsv.gz",
            "md5": "934bbdeacd",
            "size": 22710325,
            "mtime": "2022-05-18 22:34:06"
        },
        "inMeta": {
            "fname": "/hive/data/inside/cells/datasets/adultPancreas/meta.tsv",
            "md5": "7699cf188d",
            "size": 527639,
            "mtime": "2019-02-26 16:08:50"
        },
        "outMeta": {
            "fname": "/usr/local/apache/htdocs-cells/adultPancreas/meta.tsv",
            "md5": "cdfeda9e0a",
            "size": 522326,
            "mtime": "2022-05-24 18:01:35"
        },
    },
    "coords": [
        {
            "name": "coords_0",
            "shortLabel": "t-SNE",
            "md5": "3ff37334ef",
            "minX": 0,
            "maxX": 65535,
            "minY": 0,
            "maxY": 65535,
            "type": "Uint16",
            "textFname": "test.coords.tsv.gz",
            "labelMd5": "d41d8cd98f"
        }
    ],
    "topMarkers": {
        "acinar": [
            "A1CF",
        ],
        "alpha": [
            "A1BG-AS1",
        ],
        "beta": [
            "LEPR",
        ],
        "delta": [
            "SST",
            "RBP4",
        ],
        "ductal": [
            "ANXA4",
        ],
        "mesenchymal": [
            "SPARCL1",
        ],
        "nan": [
            "ERCC-00092",
        ],
        "unsure": [
            "G6PC2",
            "PCSK1",
        ]
    },
}

invalid_cellbrowser_config = deepcopy(valid_cellbrowser_config["fileVersions"])

project_name = "test-project"
output_dir = "test-output-dir"


@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:

        yield mock_get


def test_download_valid_config(mock_requests_get):

    # Set up the Mock to return a fake response when called
    mock_response = Mock()
    mock_response.json.return_value = valid_cellbrowser_config
    mock_requests_get.return_value = mock_response

    obj = CellBrowserToVitessceConfigConverter(project_name, output_dir, False)
    is_valid = obj.download_config()

    # Now you can make assertions about how the mock was used and the result of your function
    mock_requests_get.assert_called_once_with('https://cells.ucsc.edu/test-project/dataset.json')
    assert is_valid == True
    assert obj.cellbrowser_config == valid_cellbrowser_config


@pytest.fixture
def mock_end_to_end_tests():
    # Set up the Mock to return a fake response when called
    mock_response_json = Mock()
    mock_response_json.json.return_value = valid_cellbrowser_config
    mock_response_json.raise_for_status.return_value = None
    mock_response_json.content = b''

    with open('tests/data/smaller_expr_matrix.tsv.gz', 'rb') as f:
        mock_response_expr_matrix = Mock()
        mock_response_expr_matrix.content = f.read()
        mock_response_expr_matrix.raise_for_status.return_value = None

    with open('tests/data/test_meta.tsv', 'rb') as f:
        mock_response_meta = Mock()
        mock_response_meta.content = f.read()
        mock_response_meta.raise_for_status.return_value = None

    with open('tests/data/test.coords.tsv.gz', 'rb') as f:
        mock_response_coords = Mock()
        mock_response_coords.content = f.read()
        mock_response_coords.raise_for_status.return_value = None

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [mock_response_json, mock_response_expr_matrix, mock_response_meta, mock_response_coords]
        yield mock_get


@pytest.fixture
def mock_filter_cells():
    with patch('scanpy.pp.filter_cells') as mock:
        yield mock


def test_filter_based_on_marker_genes(mock_requests_get, mock_end_to_end_tests, mock_filter_cells):

    # Set up the Mock to return a fake response when called
    mock_response = Mock()
    mock_response.json.return_value = valid_cellbrowser_config
    mock_requests_get.return_value = mock_response

    inst = CellBrowserToVitessceConfigConverter(project_name, output_dir, True)
    config_is_valid = inst.download_config()

    assert config_is_valid == True
    inst.load_expr_matrix()
    inst.load_cell_metadata()
    inst.load_coordinates()

    assert inst.adata.shape == (8, 10)

    inst.filter_data()

    assert inst.adata.shape == (8, 1)

    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/dataset.json")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/exprMatrix.tsv.gz")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/meta.tsv")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/test.coords.tsv.gz")

    assert mock_end_to_end_tests.call_count == 4
    assert mock_filter_cells.call_count == 1


@pytest.fixture
def mock_makedirs():
    with patch('os.makedirs') as mock:
        yield mock

# Define a fixture for adata.write_zarr


@pytest.fixture
def mock_write_zarr():
    with patch('anndata.AnnData.write_zarr') as mock:
        yield mock


def test_end_to_end(mock_makedirs, mock_write_zarr, mock_filter_cells, mock_end_to_end_tests):
    convert(project_name, output_dir, keep_only_marker_genes=False)

    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/dataset.json")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/exprMatrix.tsv.gz")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/meta.tsv")
    mock_end_to_end_tests.assert_any_call("https://cells.ucsc.edu/test-project/test.coords.tsv.gz")

    assert mock_end_to_end_tests.call_count == 4
    assert mock_filter_cells.call_count == 1
    mock_makedirs.assert_called_once_with(os.path.dirname(join(output_dir, project_name)), exist_ok=True)
    mock_write_zarr.assert_called_once_with(join(output_dir, project_name, "out.adata.zarr"), chunks=[8, VAR_CHUNK_SIZE])


def test_end_to_end_invalid_config(mock_makedirs, mock_write_zarr, mock_filter_cells):
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = invalid_cellbrowser_config
        with pytest.raises(ValueError):
            convert(project_name, output_dir, keep_only_marker_genes=False)

        mock_get.assert_called_once_with("https://cells.ucsc.edu/test-project/dataset.json")

    assert mock_get.call_count == 1


def test_end_to_end_download_config_raises_exception(mock_makedirs, mock_write_zarr, mock_filter_cells):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("Error downloading file")

    with patch('requests.get') as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(Exception):
            convert(project_name, output_dir, keep_only_marker_genes=False)

        mock_get.assert_called_once_with("https://cells.ucsc.edu/test-project/dataset.json")

        assert mock_get.call_count == 1
    assert mock_makedirs.call_count == 0
    assert mock_write_zarr.call_count == 0
    assert mock_filter_cells.call_count == 0


def test_end_to_end_load_expr_matrix_raises_exception(mock_makedirs, mock_write_zarr, mock_filter_cells):
    mock_first_response = Mock()
    mock_first_response.json.return_value = valid_cellbrowser_config

    mock_second_response = Mock()
    mock_second_response.raise_for_status.side_effect = Exception("Error downloading file")

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [mock_first_response, mock_second_response]
        with pytest.raises(Exception):
            convert(project_name, output_dir, keep_only_marker_genes=False)

        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/dataset.json")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/exprMatrix.tsv.gz")
        assert mock_get.call_count == 2
    assert mock_makedirs.call_count == 0
    assert mock_write_zarr.call_count == 0
    assert mock_filter_cells.call_count == 0


def test_end_to_end_load_cell_metadata_raises_exception(mock_makedirs, mock_write_zarr, mock_filter_cells):
    mock_get_config = Mock()
    mock_get_config.json.return_value = valid_cellbrowser_config

    with open('tests/data/smaller_expr_matrix.tsv.gz', 'rb') as f:
        mock_response_expr_matrix = Mock()
        mock_response_expr_matrix.content = f.read()
        mock_response_expr_matrix.raise_for_status.return_value = None

    mock_response_meta = Mock()
    mock_response_meta.raise_for_status.side_effect = Exception("Error downloading file")
    assert mock_makedirs.call_count == 0
    assert mock_write_zarr.call_count == 0
    assert mock_filter_cells.call_count == 0

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [mock_get_config, mock_response_expr_matrix, mock_response_meta]
        with pytest.raises(Exception):
            convert(project_name, output_dir, keep_only_marker_genes=False)

        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/dataset.json")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/exprMatrix.tsv.gz")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/meta.tsv")
        assert mock_get.call_count == 3
    assert mock_makedirs.call_count == 0
    assert mock_write_zarr.call_count == 0
    assert mock_filter_cells.call_count == 0


def test_end_to_end_add_coords_raises_exception(mock_makedirs, mock_write_zarr, mock_filter_cells):
    mock_get_config = Mock()
    mock_get_config.json.return_value = valid_cellbrowser_config

    with open('tests/data/smaller_expr_matrix.tsv.gz', 'rb') as f:
        mock_response_expr_matrix = Mock()
        mock_response_expr_matrix.content = f.read()
        mock_response_expr_matrix.raise_for_status.return_value = None

    with open('tests/data/test_meta.tsv', 'rb') as f:
        mock_response_meta = Mock()
        mock_response_meta.content = f.read()
        mock_response_meta.raise_for_status.return_value = None

    mock_coords = Mock()
    mock_coords.raise_for_status.side_effect = Exception("Error downloading file")

    with patch('requests.get') as mock_get:
        mock_get.side_effect = [mock_get_config, mock_response_expr_matrix, mock_response_meta, mock_coords]
        with pytest.raises(Exception):
            convert(project_name, output_dir, keep_only_marker_genes=False)

        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/dataset.json")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/exprMatrix.tsv.gz")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/meta.tsv")
        mock_get.assert_any_call("https://cells.ucsc.edu/test-project/test.coords.tsv.gz")
        assert mock_get.call_count == 4
    assert mock_makedirs.call_count == 0
    assert mock_write_zarr.call_count == 0
    assert mock_filter_cells.call_count == 0
