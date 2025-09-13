#! /usr/bin/env python3

"""\
Translate a SKL decision tree classifier to C++
"""

import textwrap
import os.path
from . import petrifyml_common as pc

def dt_to_cpp(estimator, dtname="decision", regression=False):
    """\
    Turn the given estimator into a standalone C++ source string, using the given function name.

    TODO: enable passing in a set of node values for regression/score use.
    """

    ## Parallel arrays containing tree structure
    n_nodes = estimator.tree_.node_count
    children_left = estimator.tree_.children_left
    children_right = estimator.tree_.children_right
    feature = estimator.tree_.feature
    threshold = estimator.tree_.threshold
    values = estimator.tree_.value

    rtntype = "double" if regression else "int"

    cout = f"""\
    template <typename C=std::vector<double>>
    {rtntype} {dtname}(const C& args) {{"""
    if regression:
        valstr = ", ".join([("%.8g" % v) for v in values[:,0,0]]) #< TODO: robust? + flatten non-leaf values
        cout += f"""
      static const double values[{n_nodes}] = {{ {valstr} }};"""
    cout += """
      int inode = 0;
      while (1) {
        switch (inode) {"""

    for inode in range(n_nodes):
        ival = feature[inode]
        thres = threshold[inode]
        ileft = children_left[inode]
        iright = children_right[inode]
        cout += f"\n        case {inode}:"
        if children_left[inode] == children_right[inode]:
            if regression:
                cout += f"\n          return values[{inode}];"
            else:
                cout += f"\n          return {inode};"
        else:
            cout += f"\n          inode = (args[{ival}] <= {thres}) ? {ileft} : {iright}; break;"

    cout += """
        }
      }
      return -1;
    }
    """
    return textwrap.dedent(cout)


def main(args):

    try:
        from sklearn.tree import DecisionTreeClassifier
    except ImportError:
        print("sklbdt-to-cpp requires the scikit-learn Python module to be installed")

    if "/" in args.NAME:
        funcName = os.path.basename(args.NAME)
    else:
        funcName = args.NAME

    estimator = None

    # OLD demonstartion format for training an individual tree
    # if args.FILE is None:
    #     ## Demo with SKL Iris dataset
    #     print("No model given: training a demo BDT on the SKL Iris test data")
    #     from sklearn.model_selection import train_test_split
    #     from sklearn.datasets import load_iris
    #     iris = load_iris()
    #     X = iris.data
    #     y = iris.target
    #     X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
    #     estimator = DecisionTreeClassifier(max_leaf_nodes=3, random_state=0)
    #     estimator.fit(X_train, y_train)
    #     print(type(estimator))
    #     cout = dt_to_cpp(estimator, funcName)

    # TODO: OLD format for loading individual trees
    # Kept for interest
    # elif args.FILE.endswith(".pkl"):
    #     import pickle
    #     with open(args.FILE, "rb") as f:
    #         estimator = pickle.load(f)
    #     print(type(estimator))
    #     cout = dt_to_cpp(estimator, funcName)

    if args.FILE.endswith(".job") or args.FILE.endswith(".pkl"): #< NOT XML!!
        import joblib
        gbclassifier = joblib.load(args.FILE)
        print(type(gbclassifier))
        if (gbclassifier.__class__.__name__ != "GradientBoostingClassifier"):
            raise TypeError("sklbdt-to-cpp is for Gradient Boosting Classifiers (or individual trees) only")

        print(type(gbclassifier.estimators_))
        print("NEstimators", len(gbclassifier.estimators_))
        nInputs = gbclassifier.n_features_in_
        print("NFeatures", gbclassifier.n_features_in_)
        if (gbclassifier.feature_names_in_ is not None):
            print("Feature Names", gbclassifier.feature_names_in_)
            feature_names = gbclassifier.feature_names_in_
        else:
            feature_names = None
        print("NClasses", gbclassifier.n_classes_)
        print("Classes", gbclassifier.classes_)
        # estimators = gbclassifier.estimators_[0,0]
        couts = []
        for icls in range(1): #self.n_classes):
            treefns = []
            for iest in range(gbclassifier.n_estimators):
                estimator = gbclassifier.estimators_[iest, icls]
                treefn = "{}_{:03d}_{:03d}".format(funcName, iest, icls)
                tree_cc = dt_to_cpp(estimator, treefn, True)
                treefns.append(treefn)
                couts.append(tree_cc)

            # Sum over tree output-node values, based on
            #   def predict_stages ->
            #   cdef void _predict_regression_tree_inplace_fast_dense
            # from sklearn ensemble/_gradient_boosting.pyx:
            #   out[i * K + k] += scale * value[node - root_node]
            # ~ out[k] += scale * tree.value
            sumstr = " + ".join("{}(args)".format(tf) for tf in treefns)
        btree_cc = """\
    inline double sigmoid (const double x){{
        return 1./(1+exp(-x));
    }}
    template <typename C=std::vector<double>>
    double {bdtname}(const C& args) {{
      return sigmoid({scale}*({sumstr}));
    }}""".format(bdtname=funcName, scale=gbclassifier.learning_rate, sumstr=sumstr)
        couts.append(textwrap.dedent(btree_cc))
        cout = "\n\n".join(couts)

    else:
        raise Exception("Input files must be in .job or .pkl format")

    cout = "#include <vector>\n#include <cmath>\n\n" + cout

    # Write validation process into cpp file
    if args.WRITE_VALIDATION or (args.RUN_VALIDATION is not None):    
        #TODO: I think adding numpy for random numbers is probably fair?
        try:
            import numpy as np
        except:
            raise ImportError("sklbdt-to-cpp validation code writing requires numpy!")
        if args.RUN_VALIDATION is None or args.RUN_VALIDATION == []:
            testinputs = np.random.normal(size=gbclassifier.n_features_in_, loc=0, scale=2)
        else:
            testinputs = args.RUN_VALIDATION
            if len(testinputs) != gbclassifier.n_features_in_:
                raise Exception("Classifier expects {} inputs, you have provided {}".format(gbclassifier.n_features_in_, len(testinputs)))

        cout = "#include <iostream> \n" + cout
        cout += """
        int main(){{
            std::cout << {}(std::vector<double>{{{}}}) << std::endl;;
        }}""".format(funcName, ", ".join(map(str, testinputs)))

        executeName = args.NAME if args.NAME[0] == "/" else "./"+args.NAME

        print("""\n\nA main as been added to your .cc file to enable testing. Compile with
              g++ {}.cc -o {} """.format(args.NAME, args.NAME))
        print("""And execute with
              {}
        """.format(executeName))
        
    if args.VERBOSE:
        print(cout)
    with open(args.NAME + ".cc", "w") as f:
        f.write(cout)

    # Run testing if requested
    if args.RUN_VALIDATION is not None:
        if args.FILE.endswith(".job") or args.FILE.endswith(".pkl"):
            print ("\nRunning validation test...")
            if feature_names is not None:
                import pandas as pd
                testinputs_formatted = pd.DataFrame([testinputs], columns=feature_names)
            else:
                testinputs_formatted = [testinputs]
            targetOut = gbclassifier.predict_proba(testinputs_formatted)
            print("    Input is [{}]".format(", ".join(map(str, testinputs))))
            print("    target output is: {}".format(targetOut))
            try:
                import subprocess
            except:
                raise ImportError("Can't compile without subprocess, not running full validation")
            compile_command = ["g++", "{}.cc".format(args.NAME), "-o", args.NAME]
            compile_result = subprocess.run(compile_command, check=True, capture_output=True, text=True)
            if compile_result.returncode != 0:
                raise Exception("Compilation failed with output\n{}".format(compile_result.stderr()))
            print("BDT compiled...")
            execute_command = [executeName]
            execute_result = subprocess.run(execute_command, check=True, capture_output=True, text=True)
            print("    cpp output result is {}".format(float(execute_result.stdout)))
            if (np.isclose(float(execute_result.stdout), targetOut[0][1])):
                print ("BDTs agree! Test passed")
            else:
                raise Exception("BDTs do not agree! Debugging needed!")
        
        
def make_sklbdt_to_cpp_argparser():
    ap = pc.get_args_parser(desc=["scikit-learn BDT", "C++ code"])
    ap.add_argument("--write-validation", dest="WRITE_VALIDATION", action="store_true",
                    help="Add a main function to the cpp file for easy testing")
    ap.add_argument("--run-validation", dest="RUN_VALIDATION", nargs="*", 
                    help="Add a main function to the cpp file, run it, and compare output to skl for a supplied/random input (requires g++)")
    return ap

def main_wrapper():
    args = make_sklbdt_to_cpp_argparser().parse_args()
    main(args)

if __name__ == "__main__":
    main_wrapper()
