import pytest
import os
import numpy as np
from pathlib import Path
from petrifyml.mvautils_lgbm_to_onnx import main
from petrifyml.mvautils_common_utils import make_mvautils_argparser
from test_common import load_and_infer_onnx

# Get the directory of the current test file
THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = THIS_DIR / "testdata/mvautils" # Path to the co-located test data direc

def test_mvautilslgbm_to_onnx_classifier(tmp_path):
    # Get test lwtnn json, convert
    rootpath = TEST_DATA_DIR / "lgbm_example.root"
    assert rootpath.exists(), "Cannot find test data!"
    parser = make_mvautils_argparser("lgbm")
    tmp_onnx_outputpath = str(tmp_path)+"/lgbm_example"
    args = parser.parse_args([str(rootpath), "-n", tmp_onnx_outputpath, "--ir-version", "10", "--opset", "22", "--classifier"])
    assert parser.description == "Convert a MVAUtils lgbm to ONNX"
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [
                {"input": [11.77401830736426, 6.320129680499643, 6.873258928120649, 13.547869330829844, 8.840225923883857],
                 "output": [0.821521759033]},
                 {"input": [3.77401830736426, -2.320129680499643, 0.873258928120649, -1.547869330829844, 0.840225923883857],
                 "output": [0.519579648972]},
                 {"input": [-3.77401830736426, -2.320129680499643, -0.873258928120649, -1.547869330829844, 0.840225923883857],
                 "output": [0.184835448861]},
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()



def test_mvautilslgbm_to_onnx_regressor(tmp_path):
    # Get test lwtnn json, convert
    rootpath = TEST_DATA_DIR / "lgbm_regressor.root"
    assert rootpath.exists(), "Cannot find test data!"
    parser = make_mvautils_argparser()
    tmp_onnx_outputpath = str(tmp_path)+"/lgbm_regressor"
    args = parser.parse_args([str(rootpath), "-n", tmp_onnx_outputpath, "--ir-version", "10", "--opset", "22"])
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [
                {"input": [7.792113708687661, 8.525273936993766, 17.507378246459908, 10.317131287015311, 8.502460889771033],
                 "output": [2.59791088104]},
                 {"input": [7.792113708687661, 0.525273936993766, 17.507378246459908, -1.317131287015311, 8.502460889771033],
                 "output": [7.57260322571]},
                 {"input": [-7.792113708687661, 0.525273936993766, -2.507378246459908, -1.317131287015311, -2.502460889771033],
                 "output": [-2.24816441536]},
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()