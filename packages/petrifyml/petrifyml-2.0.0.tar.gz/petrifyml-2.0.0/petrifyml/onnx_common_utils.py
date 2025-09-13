from onnx import TensorProto
from onnx.helper import make_operatorsetid

def get_onnx_float_type(typestring: str):
    if typestring == "float":
        return TensorProto.FLOAT
    elif typestring == "double":
        return TensorProto.DOUBLE
    elif typestring == "float16":
        return TensorProto.FLOAT16
    else:
        print(f"Float type \"{typestring}\" is not recognised")

def get_numpy_float_typestring(typestring: str):
    if typestring == "float":
        return "np.float32"
    elif typestring == "double":
        return "np.float64"
    elif typestring == "float16":
        return "np.float16"
    else:
        print(f"Float type \"{typestring}\" is not recognised")


def add_onnx_argparse_options(ap):
    ap.add_argument("--human-readable-onnx", dest="TEXT_ONNX",action="store_true",
                    help="write a human-readable version of the onnx protobuf for debugging")
    ap.add_argument("--float-type", dest="FLOAT_TYPE", default="float",
                    type=str, choices=["float", "double", "float16"] ,
                    help="Which floating-point type to use in onnx: float (default), double, or float16")
    ap.add_argument("--opset-version", "--opset", type=int, dest="OPSET_VER", default=None,
                    help="specify the onnx opset. Defaults to the latest supported by the local onnx python module.")
    ap.add_argument("--ir-version", type=int, default=None, dest="IR_VER", help="Specify onnx IR version")

    return ap

def make_opset_info(opset):
    if opset is not None:
        return [make_operatorsetid("", opset)]
    return None
