import pytest
import os
import numpy as np
from pathlib import Path
import json
from petrifyml.tmvamlp_to_onnx import main, get_tmvamlp_argparser
from test_common import load_and_infer_onnx

# Get the directory of the current test file
THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = THIS_DIR / "testdata/tmvamlp_to_onnx" # Path to the co-located test data direc

def test_tmvamlp_to_onnx_classifier(tmp_path):
    # Get test TMVA MLP xml, convert
    rootpath = TEST_DATA_DIR / "tmvamlp_example.xml"
    assert rootpath.exists(), "Cannot find test data!"
    parser = get_tmvamlp_argparser()
    tmp_onnx_outputpath = os.path.join(str(tmp_path), "tmvamlp_example")
    args = parser.parse_args([str(rootpath), "-n", tmp_onnx_outputpath])
    assert parser.description == "Convert a TMVA MLP to ONNX"
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    valuespath = TEST_DATA_DIR / "values_example.json"
    with open(valuespath, 'r') as file:
        datasets = json.load(file)

    for d in datasets:
        output = load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]])
        assert np.isclose(d["output"], output)
