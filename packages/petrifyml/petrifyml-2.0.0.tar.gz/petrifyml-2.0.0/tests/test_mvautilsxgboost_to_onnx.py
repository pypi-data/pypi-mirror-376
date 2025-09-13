import pytest
import os
import numpy as np
from pathlib import Path
from petrifyml.mvautils_xgboost_to_onnx import main
from petrifyml.mvautils_common_utils import make_mvautils_argparser
from test_common import load_and_infer_onnx

# Get the directory of the current test file
THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = THIS_DIR / "testdata/mvautils" # Path to the co-located test data direc

def test_mvautilsxgboost_to_onnx_classifier(tmp_path):
    # Get test lwtnn json, convert
    rootpath = TEST_DATA_DIR / "xgb_example.root"
    assert rootpath.exists(), "Cannot find test data!"
    parser = make_mvautils_argparser()
    tmp_onnx_outputpath = str(tmp_path)+"/xgb_example"
    args = parser.parse_args([str(rootpath), "-n", tmp_onnx_outputpath, "--ir-version", "10", "--opset", "22", "--classifier"])
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [
                {"input": [11.77141578166851, 9.112047281959823, 9.350429192819371, 11.083870210067369, 11.907554045972736],
                 "output": [0.976327776909]},
                {"input": [-1.77141578166851, 0.112047281959823, -7.350429192819371, 4.083870210067369, 0.907554045972736],
                 "output": [0.133843764663]},
                {"input": [-3.77141578166851, -0.112047281959823, -2.350429192819371, 3.083870210067369, 1.907554045972736],
                 "output": [0.690402150154]}
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()