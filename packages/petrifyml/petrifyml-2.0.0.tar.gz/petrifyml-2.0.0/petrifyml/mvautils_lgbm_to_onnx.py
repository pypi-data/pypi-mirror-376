#! /usr/bin/env python
# -*- python -*-

"""
Translate a ROOT file containing a MVAUtils implementation of an lgbm bdt into onnx.

MVAUtils can import models from several frameworks into their ROOT formats.
These formats are NOT the same. This converter will only work if the original
BDT came from lgbm (if unsure, a quick inspection of tree names should help).

The script uses onnx.helper and the onnx TreeEnsemble operator to construct
the onnx model graph directly (no intermediate formats/codes are used).

Requires the onnx, uproot and numpy python modules. Does not require ROOT or
Athena (which is normally how MVAUtils is accessed).
That said, it is always good practice to run validation yourself.
"""

from . import mvautils_common_utils as mcu
try:
    import onnx
    import uproot
except:
    print("Conversion of mvautils files requires uproot and onnx python modules")
    print("Try `pip install petrifyml[mvautils]` to automatically install all dependencies")
    exit(1)

def get_lgbm_arrays_from_root(root_file_path: str, treeName=None):
    if treeName is None:
        file = uproot.open(root_file_path)
        keys = file.keys()
        # Deal with  ""...;1", "...;2" etc issues with ROOT files.
        abridged_keys = list(set([k.split(";")[0] for k in keys]))
        if len(abridged_keys) > 1:
            if "lgbm" not in keys:
                print(f"Error: file {root_file_path} contains multiple trees, please specify at command line")
                exit(1)
            else:
                print(f"Warning: file {root_file_path} contains multiple trees, defaulting to 'lgbm'.")
                print("    This may NOT be the behaviour you want")
                treeName = "lgbm"
                tree = file["lgbm"]
        else:
            treeName = abridged_keys[0]
            if not treeName.startswith("lgbm"):
                print(f"Warning: file {root_file_path} contains tree {treeName}. This name seems suspicious.")
                print(f"    Does this ROOT file definitely come from lgbm?")
            tree = file[treeName]
            print(f"Inferred mvautils tree name '{treeName}'")
            
    else:
        try:
            tree = uproot.open(root_file_path)[treeName]
        except uproot.exceptions.KeyInFileError:
            print(f"Error: Tree '{treeName}' not found in ROOT file: {root_file_path}")
            exit(1)
        except Exception as e:
            print(f"Error opening ROOT file: {e}")
            exit(1)

    vars_array = tree["vars"].array(library="np")
    values_array = tree["values"].array(library="np")

    return vars_array, values_array, treeName

def main(args):
    from .onnx_common_utils import get_onnx_float_type, make_opset_info, get_numpy_float_typestring

    print("Initialising...")

    vars_array, values_array, treeName = get_lgbm_arrays_from_root(args.FILE)

    if (args.N_FEATURES is None):
        args.N_FEATURES = mcu.get_n_features_from_variables(vars_array, 3)
        print(f"Inferred that there are {args.N_FEATURES} input features from ROOT file.")

    m = mcu.build_onnx_model(vars_array, values_array, args.N_FEATURES, 
                             None, args.NAME+".onnx", 
                             floattype=get_onnx_float_type(args.FLOAT_TYPE),
                             opset=make_opset_info(args.OPSET_VER), ir_version=args.IR_VER,
                             aggregate_function=1, node_mode=0, isClassifier=args.CLASSIFIER)
    
    if args.WRITE_VALIDATION:
        mcu.make_mvautils_validation(args.FILE, args.NAME+".onnx",
                                         ninputs=args.N_FEATURES,
                                         floatstring=get_numpy_float_typestring(args.FLOAT_TYPE),
                                         treeName=treeName, isClassifier=args.CLASSIFIER)
    
    if (args.TEXT_ONNX):
        with open(args.NAME+".text.onnx", "w") as f:
            f.write(onnx.printer.to_text(m))
        print(f"Written text protobuf of onnx file to {args.NAME}.text.onnx")

def main_wrapper():
    main(mcu.get_user_mvautils_args("lgbm"))

if __name__ == "__main__":
    main_wrapper()