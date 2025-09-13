import pytest
import os
import numpy as np
from pathlib import Path
from petrifyml.lightweightnn_to_onnx import main, make_lightweightnn_argparser
from test_common import load_and_infer_onnx

# Get the directory of the current test file
THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = THIS_DIR / "testdata/lwtnn" # Path to the co-located test data direc

def test_lwtnn_relu_softmax(tmp_path):
    # Get test lwtnn json, convert
    jsonpath = TEST_DATA_DIR / "2_relu5_softmax2.json"
    assert jsonpath.exists(), "Cannot find test data!"
    parser = make_lightweightnn_argparser()
    tmp_onnx_outputpath = str(tmp_path)+"/lwtnn_relu_softmax"
    args = parser.parse_args([str(jsonpath), "-n", tmp_onnx_outputpath, "--ir-version", "10", "--opset", "22"])
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [{"input": [-0.36374810909985444, -3.8592096722795612],
                "output": [0.999996871745, 3.12825532346e-06]},
                {"input": [0.36374810909985444, 3.8592096722795612],
                "output": [0.00297821062839, 0.997021789372]},
                {"input": [0.36374810909985444, -0.8592096722795612],
                "output": [0.506182358339, 0.493817641661]}
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()


def test_lwtnn_elu_sigmoid(tmp_path):
    # Get test lwtnn json, convert
    jsonpath = TEST_DATA_DIR / "2_elu5_sigmoid1.json"
    assert jsonpath.exists(), "Cannot find test data!"
    parser = make_lightweightnn_argparser()
    tmp_onnx_outputpath = str(tmp_path)+"/lwtnn_elu_sigmoid"
    args = parser.parse_args([str(jsonpath), "-n", tmp_onnx_outputpath, "--ir-version", "10", "--opset", "22"])
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [{"input": [0.8469157917956136, -2.8870062853678435],
                "output": [0.963640072675]},
                {"input": [0.8469157917956136, 2.8870062853678435],
                "output": [0.0369105037718]},
                {"input": [1.8469157917956136, -0.8870062853678435],
                "output": [0.528945202896]}
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()


def test_lwtnn_relu_tanh(tmp_path):
    # Get test lwtnn json, convert
    jsonpath = TEST_DATA_DIR / "2_relu5_tanh1.json"
    assert jsonpath.exists(), "Cannot find test data!"
    parser=make_lightweightnn_argparser()
    tmp_onnx_outputpath = str(tmp_path)+"/lwtnn_relu_tanh"
    args = parser.parse_args([str(jsonpath), "-n", tmp_onnx_outputpath, "--ir-version", "10",
                             "--opset", "22", "--float-type", "double"])
    main(args)
    tmp_onnx_outputpath+=".onnx"
    assert (os.path.exists(tmp_onnx_outputpath))

    # Dataset of inputs and (pre-calculated) outputs
    # TODO: There's got to be a better long term solution than hard-coding here
    datasets = [{"input": [-1.7838567397321674, -2.436368962311989],
                "output": [0.806766513599]},
                {"input": [-1.7838567397321674, 2.436368962311989],
                "output": [-0.965198012014]},
                {"input": [0.7838567397321674, 1.436368962311989],
                "output": [-0.65787034886]}
                ]
    
    for d in datasets:
        out = np.array(load_and_infer_onnx(tmp_onnx_outputpath, [d["input"]]))
        #TODO: better measure than isclose?
        assert np.isclose(out, d["output"]).all()