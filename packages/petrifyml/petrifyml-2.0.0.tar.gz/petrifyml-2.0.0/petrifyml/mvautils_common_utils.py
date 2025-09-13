"""
Several functions that are useful across the multiple different MVAUtils types
(xgboost, lgbm)

The reason this factorisation works (at least a bit) is that while the exact
ROOT structure is not exactly the same, the trees are both stored in a 
"pre-order traversal" layout.
"""
try:
    from onnx import helper, TensorProto
    import numpy as np
    import onnx
except:
    print("Conversion of mvautils files requires uproot, numpy and onnx python modules")
    print("Try `pip install petrifyml[mvautils]` to automatically install all dependencies")
    exit(1)

def get_n_features_from_variables(vars_array, trees_to_test=5):
    """
    Guesses the number of expected input features from the "vars" array

    Samples the first `trees_to_test` trees in the forest. Will fail if
    all of the first `trees_to_test` do not use the final input feature.
    In principle even setting `trees_to_test` to the forest size could fail,
    if an input is never used.
    """
    trees_to_test = min(trees_to_test, len(vars_array))
    max_vars = max([int(max(i)) for i in vars_array[0:trees_to_test]])
    return max_vars+1

def find_right_child(start_idx, vars_)->int:
    """
    Finds the index of the right child node in a depth-first flattened tree.
    Assumes left child is at start_idx + 1, and all left children are expanded recursively.
    """
    count = 0
    idx = start_idx + 1
    while idx < len(vars_):
        if vars_[idx] == -1:
            if count == 0:
                return idx + 1
            else:
                count -= 1
        else:
            count += 1
        idx += 1
    raise RuntimeError(f"Failed to find right child from node {start_idx}.")

def convert_forest_to_onnx_attributes(all_vars, all_values, all_default_left=None, floattype=TensorProto.FLOAT, node_mode=1):
    """
    Converts a forest of trees into ONNX attributes for TreeEnsemble.
    """
    nodes_featureids = []

    nodes_truenodeids = []
    nodes_falsenodeids = []
    nodes_trueleafs = []
    nodes_falseleafs = []
    nodes_missing_value_tracks_true = []

    nodes_modes = []
    nodes_splits = []

    leaf_targetids = []
    leaf_weights = []

    tree_roots = []

    branch_offset=0
    leaf_offset=0
    #TODO: if there is a cleaner way to loop over lists, one of which may be none, I'd be glad to know.
    for vars_, values_, default_left_ in zip(all_vars, all_values, 
                    all_default_left if all_default_left is not None else np.zeros(shape=all_vars.shape)):
        tree_roots.append(branch_offset)

        branches = []
        leaves = []

        # TODO: this approach will not work on trees containing a single node. Can this ever happen?
        # (forbidden in onnxruntime, technically possible in MVAUtils? Very unlikely either way)
        def recurse_func(orig_idx):
            # First things first: branch or leaf
            if (vars_[orig_idx] == -1):
                leaves.append(orig_idx)
                return orig_idx
            else:
                branches.append(orig_idx)
                recurse_func(orig_idx+1)
                recurse_func(find_right_child(orig_idx, vars_))
        recurse_func(0)
            
        for b in branches:
            nodes_featureids.append(vars_[b])
            nodes_modes.append(node_mode) # Enum: 0="BRANCH_LEQ"; 1="BRANCH_LE"
                                  # Based on xgboost docs I expected <= BUT 
                                  # MVAUtils NodeXGBoost::GetNext uses <
            nodes_splits.append(values_[b])
            if all_default_left is not None:
                nodes_missing_value_tracks_true.append(bool(default_left_[b]))

            lindex = b+1
            rindex = find_right_child(b, vars_)
            # is left tree or leaf
            if (vars_[lindex] == -1):
                nodes_trueleafs.append(1)
                nodes_truenodeids.append(leaves.index(lindex)+leaf_offset)
            else:
                nodes_trueleafs.append(0)
                nodes_truenodeids.append(branches.index(lindex)+branch_offset)

            # is right tree or leaf
            if (vars_[rindex] == -1):
                nodes_falseleafs.append(1)
                nodes_falsenodeids.append(leaves.index(rindex)+leaf_offset)
            else:
                nodes_falseleafs.append(0)
                nodes_falsenodeids.append(branches.index(rindex)+branch_offset)

        for l in leaves:
            leaf_targetids.append(0) # I don't think xgboost can handle multi-option.
            leaf_weights.append(values_[l])

        leaf_offset+=len(leaves)
        branch_offset+=len(branches)

    if all_default_left is None:
        nodes_missing_value_tracks_true = None
       
    return {
        "tree_roots": tree_roots,
        "nodes_featureids": nodes_featureids,
        "nodes_modes": helper.make_tensor(vals = nodes_modes,
                                        dims = [len(nodes_modes)],
                                        name="nodes_modes",
                                        data_type=TensorProto.UINT8),
        "nodes_splits": helper.make_tensor(vals = nodes_splits,
                                        dims = [len(nodes_splits)],
                                        name="nodes_splits",
                                        data_type=floattype),
        "nodes_truenodeids": nodes_truenodeids,
        "nodes_falsenodeids": nodes_falsenodeids,
        "nodes_trueleafs": nodes_trueleafs,
        "nodes_falseleafs": nodes_falseleafs,
        "nodes_missing_value_tracks_true": nodes_missing_value_tracks_true,

        "leaf_targetids": leaf_targetids,
        "leaf_weights": helper.make_tensor( vals=leaf_weights,
                                            dims = [len(leaf_weights)], 
                                            name="leaf_weights",
                                            data_type=floattype
                                           )
    }

def build_onnx_model(all_vars, all_values, n_features: int, all_default_left=None,
                    filename="bdt_forest.onnx", floattype=TensorProto.FLOAT,
                    input_name="X", output_name="Y", opset=None, ir_version=None,
                    aggregate_function:int=1, node_mode=1, isClassifier:bool=False):
    """
    Builds and saves an ONNX TreeEnsemble model.

    Parameters:
        all_vars: The 2D array (n_trees, n_leaves) of right children indices
            (-1 for leaves), in "depth-first flattened" structure
        all_values: The 2D array (n_trees, n_leaves) of split values/weights,
            each tree in "depth-first flattened" structure.
        n_features (int): number of input features.
        all_default_left: Treat NaN as true or false at each node, 2D array
            as for other inputs, defaults to None.
        filename (str): output filename
        floattype: TensorProto floating-point type to be used in ONNX file.
        input_name: Name of the inputs in ONNX. Defaults to 'X'
        output_name: Name of the inputs in ONNX. Defaults to 'Y'
        opset: ONNX opset (defaults to system default)
        ir_version: ONNX intermediate representation version (defaults to 
            system default)
        aggregate_function (int): enum for tree aggregation, see 
            https://onnx.ai/onnx/operators/onnx_aionnxml_TreeEnsemble.html
            Default is 1 (SUM).
        node_mode: enum for operation at each node, see 
            https://onnx.ai/onnx/operators/onnx_aionnxml_TreeEnsemble.html.
            Default is 1 (<).
    """
    attrs = convert_forest_to_onnx_attributes(all_vars, all_values, all_default_left,
                                              floattype=floattype, node_mode=node_mode)

    # Model input/output
    inputs = [helper.make_tensor_value_info(input_name, floattype, [None, n_features])]
    outputs = [helper.make_tensor_value_info(output_name, floattype, [None, 1])] # n_outputfeatures=1

    # TreeEnsemble node
    node = helper.make_node(
        "TreeEnsemble",
        inputs=["X"],
        outputs=["Y"] if (not isClassifier) else ["Z"],
        domain="ai.onnx.ml",
        n_targets=1,
        aggregate_function=aggregate_function, # Aggregate function 1 = sum
        # TODO: move back to post_transform once ONNXruntime fixes their implementation.
        # (https://github.com/microsoft/onnxruntime/issues/24862)
        # post_transform=(2 if isClassifier else 0),
        post_transform = 0,
        **attrs
    )

    if isClassifier:
        # TODO: temporary workaround while onnxruntime get their ... stuff together.
        # (see comment above)
        sigmoid_node = helper.make_node(
            "Sigmoid",
            inputs=["Z"],
            outputs=["Y"],
        )
        nodes = [node, sigmoid_node ]
    else:
        nodes = [node]

    # Assemble graph & model
    graph = helper.make_graph(nodes, "BDT_Forest", inputs, outputs)
    # TODO it really sucks that passing ir_version=None does not just auto-default it!
    # Get with it, onnx!
    if ir_version is not None:
        model = helper.make_model(graph,
                                opset_imports = opset,
                                ir_version=ir_version)
    else:
        model = helper.make_model(graph,
                                opset_imports = opset)

    onnx.save(model, filename)
    
    print(f"Onnx model saved to {filename}")
    return model


def make_mvautils_validation(rootfile: str, onnxfile:str, ninputs: int, 
                                treeName = "xgboost", floatstring="np.float32",
                                isClassifier:bool = False) -> None:
    import os
    import shutil

    if (not os.path.isfile(rootfile)):
        print(f"MVAUtils Root file {rootfile} not found")
        return
    if (not os.path.isfile(onnxfile)):
        print(f"MVAUtils Root file {onnxfile} not found")
        return
    valdir=f"mvautils_{treeName}_valdir"
    if (os.path.isdir(valdir)):
        shutil.rmtree(valdir)
    os.mkdir(valdir)
    
    testinputs = np.random.normal(loc=10, scale=3, size=(ninputs))
    testinputsnumpy =  "np.array([[{}]], dtype={})".format(", ".join(map(str, testinputs)), floatstring)
    testinputcpp = "{}".format(", ".join(map(str, testinputs)))
    
    readmestring=f"""# mvautils to {treeName} validation directory
This directory contains three scripts:
- testmvautils.cxx: ROOT macro that checks the intended MVAUtils score. \
Needs to be run with ROOT in an Athena environment to access MVAUtils \
(this may be difficult for those outside of ATLAS, though e.g. SimpleAnalysis \
docker containers may work). Outputs to testmvautils.csv
- testonnx.py: python script that tests the onnx implementation. \
Needs to be run in a python environment with access to onnx runtime. \
Outputs to testonnx.csv
- validator.py. Check the outputs match.
You may need to run the scripts non-locally: this is fine, just copy back the \
csv file afterwards.

Run the first two scripts in any order, then run validator.py.

Just using random input can sometimes avoid engaging with some of the trickier \
aspects of converting BDT formats (integer values, what happens on ==, etc).
If you know the expected scale and data type, consider overwriting the random \
inputs (in both files!) with something more realistic.

In general, it might be better to think of this directory more as inspiration \
(that has written most of the boilerplate for you), rather than a comprehensive \
test. 

## onnxruntime can't load onnx files?
Sometimes, the version of onnx we used to make the onnx files is a bit ahead of
the version of onnxruntime we try and use for inferrence (even if installed at
the same time). If this is the case, regenerate the model with an older opset
and or ir-version (opset 22, ir 10 should work).
"""
    with open (f"{valdir}/readme.md", "w") as f:
        f.write(readmestring)
    
    onnxstring=f"""
import onnxruntime as ort
import numpy as np

# Load the model
session = ort.InferenceSession("../{onnxfile}", providers=["CPUExecutionProvider"])

# Inspect input name and shape
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

n_features = session.get_inputs()[0].shape[1]

X_test = {testinputsnumpy}

# Run inference
Y_pred = session.run([output_name], {{input_name: X_test}})
print("ONNX Output: ", Y_pred)
with open("testonnx.csv", "w") as f:
    f.write(str(Y_pred[0][0][0]))
"""
    with open(f"{valdir}/testonnx.py", "w") as f:
        f.write(onnxstring)

    rootstring=f"""#include "MVAUtils/BDT.h"
#include <fstream>
#include <iomanip>

int testmvautils(){{
    TFile* f = TFile::Open("../{rootfile}");
    TTree* tree = nullptr;
    f->GetObject("{treeName}", tree);
    MVAUtils::BDT my_bdt(tree);

    std::vector<float> testinputs = {{{testinputcpp}}};
    float output = my_bdt.{"GetClassification" if isClassifier else "GetResponse"}(testinputs);
    std::cout << output << std::endl;
    std::ofstream outfileroot("testmvautils.csv");
    outfileroot << std::setprecision(10) << output << std::endl;
    outfileroot.close();
    return 0;
}}          
"""
    with open(f"{valdir}/testmvautils.cxx", "w") as f:
        f.write(rootstring)

    validatestring="""
import numpy as np
import os

if not os.path.isfile("testmvautils.csv"):
    print("testmvautils.csv is missing, cannot validate.")
    exit(1)
if not os.path.isfile("testonnx.csv"):
    print("testonnx.csv is missing, cannot validate.")
    exit(1)

inputonnx = np.genfromtxt("testonnx.csv")
inputmvautils = np.genfromtxt("testmvautils.csv")

print(inputonnx, inputmvautils)

if np.isclose(inputonnx, inputmvautils):
    print("onnx ({}) and MVAutils ({}) agree!".format(inputonnx,inputmvautils))

else:
    print("onnx ({}) and MVAutils ({}) do not agree!".format(inputonnx,inputmvautils))
    
"""
    with open(f"{valdir}/validator.py", "w") as f:
        f.write(validatestring)
    print(f"Written validation resources to {valdir}. See {valdir}/readme.md for instructions.")


def add_mvautils_argparse_options(ap):
    ap.add_argument("--write-validation", dest="WRITE_VALIDATION", action="store_true",
                        help="Write example validation scripts (requires pyROOT+MVAUtils - e.g. via Athena - to run).")
    ap.add_argument("--nf", "--nfeatures", dest="N_FEATURES", default=None, type=int,
                        help="Number of input features. If None, the script will try and guess, though this is not guarunteed to work.")
    ap.add_argument("--classifier", action="store_true", dest="CLASSIFIER",
                        help="""Assume that the BDT is a classifier (Add a sigmoid post-transform).\n \
Note that MVAUtils does not store this info in file, rather allows the Tree to be called as either regressor or classifier""")
    return ap

def make_mvautils_argparser(mvautils_type=""):
    from . import petrifyml_common as pc
    from .onnx_common_utils import add_onnx_argparse_options

    # TODO: I use -n for the output, it is a little misleading in this context...
    ap = pc.get_args_parser(desc=[f"MVAUtils {mvautils_type}", "ONNX"])
    add_onnx_argparse_options(ap)
    add_mvautils_argparse_options(ap)

    return ap

def get_user_mvautils_args(mvautils_type):
    ap = make_mvautils_argparser(mvautils_type)
    # Check the user hasn't asked us to run validation
    _args, unused =  ap.parse_known_args()
    for flag in unused:
        if flag == "--run-validation":
            ap.error("'--run-validation is not supported for mvautils.\nUse --write-validation and follow the running instructions.")
    return ap.parse_args()
