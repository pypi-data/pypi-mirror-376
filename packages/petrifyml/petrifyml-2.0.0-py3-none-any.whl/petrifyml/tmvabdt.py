#! /usr/bin/env python3

"""\
Translate a TMVA boosted decision tree classifier to C++ or Python

"""

import textwrap
import os.path
import numpy as np
from . import petrifyml_common as pc

def parse_type(type_string):
    "Parse a variable type from a string"
    import numpy as np
    if type_string=="D" or type_string=="F":
        # TMVA cannot differentiate between float and double
        return "f"
    raise TypeError(f"Type '{type_string}' is not understood.")

def get_properties(input_file, property_name, item_name, testinputs=None, input_list=None, verbose=False):
    "Manually parse the XML file to obtain the property names and types"
    from array import array

    if verbose:
        print(f"PROPERTY NAME: {property_name}")

    props = []
    # TODO: Does this code ever get used?
    if input_list:
        inputval = 0
        for p in input_list.split(","):
            if ":" in p:
                prop_name, prop_type = p.split(":")
            else:
                prop_name = p
                prop_type = "f"
            prop_type_arr = array(parse_type(prop_type), [inputval if testinputs is None else testinputs[inputval]])
            props.append( (prop_name, prop_type_arr) )
            inputval+=1
    else:
        inputval = 0
        import xml.etree.ElementTree as ET
        xtree = ET.parse(input_file)
        xvars = xtree.getroot().find(property_name)
        for xvar in xvars.findall(item_name): # strip plural "s"
            prop_name = xvar.get("Label")
            prop_type = xvar.get("Type")
            prop_type_arr = array(parse_type(prop_type), [inputval if testinputs is None else testinputs[inputval]])
            props.append( (prop_name, prop_type_arr) )
            inputval+=1

    if verbose:
        print(f"Found {property_name}: {props}")

    return props


def get_variables(args):
    "Manually parse the XML file to obtain the variable names and types"
    if args.RUNMAIN is None or args.RUNMAIN == []:
        testinputs = None
    else:
        testinputs = [float(f) for f in args.RUNMAIN]
    return get_properties(args.FILE, "Variables", "Variable", testinputs, args.VARIABLES, args.VERBOSE)


def add_variables_to_reader(reader, args):
    vars = get_variables(args)

    if args.VARIABLES is None:
        makeVarNameList = True
        args.VARIABLES = []
    else:
        makeVarNameList = False

    for var_name, var_type in vars:
        print(var_name, var_type, input)
        try:
            #print(var_type, var_type)
            if makeVarNameList:
                args.VARIABLES.append((var_name, var_type))
                reader.AddVariable(var_name, args.VARIABLES[-1][1])
            else:
                reader.AddVariable(var_name, var_type)
            
        except TypeError as te:
            print(f"\nERROR: Type '{var_type}' is not recognised by TMVA.")
            raise te

def printNodes(node, depth=0):
    nodetype = node.GetNodeType()
    if nodetype == 1:
        nodestr = "SIG<type={}>".format(nodetype)
    elif nodetype == -1:
        nodestr = "BKG<type={}>".format(nodetype)
    else:
        nodestr = "DECISION<type={}, cutidx={}, cutval={}, cutdir={}>".format(
              nodetype, node.GetSelector(), node.GetCutValue(), node.GetCutType())
    print(depth*"  " + nodestr)
    if node.GetNodeType() == 0:
        printNodes(node.GetLeft(), depth+1)
        printNodes(node.GetRight(), depth+1)


def mkcxxiftree(node, depth=0, regression=False, multiClass=False, nClasses=-1):
    nodetype = node.GetNodeType()
    indent = depth * "  "
    cout = ""
    if nodetype != 0: # leaf node
        cout += "{}return {};".format(indent, node.GetResponse() if (regression or multiClass) else nodetype)
    else: # decision node
        cmp = ">=" if node.GetCutType() else "<"
        if node.GetNFisherCoeff() == 0: # cut on raw feature
            cout += indent + "if (args[{}] {} {}) {{\n".format(node.GetSelector(), cmp, node.GetCutValue())
        else: # cut on a Fisher discriminant (= linear combination of features)
            if regression:
                print("Fisher cut used for regression!?") #< throw a more controlled / less repetitive warning?
            cutvalstr = str( node.GetFisherCoeff(node.GetNFisherCoeff()-1) )
            for ivar in range(node.GetNFisherCoeff()-1):
                cutvalstr += " + {}*args[{}]".format(node.GetFisherCoeff(ivar), ivar);
                cout += indent + "double fisher = {};\n".format(cutvalstr)
                cout += indent + "if (fisher {} {}) {{\n".format(cmp, node.GetCutValue())
        cout += mkcxxiftree(node.GetRight(), depth+1, regression, multiClass, nClasses)
        cout += "\n{}}} else {{\n".format(indent)
        cout += mkcxxiftree(node.GetLeft(), depth+1, regression, multiClass, nClasses)
        cout += "\n{}}}".format(indent)
    return cout


def mkpyiftree(node, depth=0, regression=False, multiClass=False, nClasses=-1):
    nodetype = node.GetNodeType()
    indent = depth * "  "

    cout = ""
    if nodetype != 0: # leaf node
        cout += "{}return {} # {} \n".format(indent, node.GetResponse() if  (regression or multiClass) else nodetype, nodetype)
    else: # decision node
        cmp = ">=" if node.GetCutType() else "<"
        if node.GetNFisherCoeff() == 0: # cut on raw feature
            cout += indent + "if args[{}] {} {}:\n".format(node.GetSelector(), cmp, node.GetCutValue())
        else: # cut on a Fisher discriminant (= linear combination of features)
            if regression:
                print("Fisher cut used for regression!?") #< throw a more controlled / less repetitive warning?
            cutvalstr = str( node.GetFisherCoeff(node.GetNFisherCoeff()-1) )
            for ivar in range(node.GetNFisherCoeff()-1):
                cutvalstr += " + {}*args[{}]".format(node.GetFisherCoeff(ivar), ivar);
                cout += indent + "fisher = {}\n".format(cutvalstr)
                cout += indent + "if fisher {} {}:\n".format(cmp, node.GetCutValue())
        cout += mkpyiftree(node.GetRight(), depth+1, regression, multiClass, nClasses)
        cout += indent + "else:\n"
        cout += mkpyiftree(node.GetLeft(), depth+1, regression, multiClass, nClasses)
    return cout


def dt_to_cpp(tree, dtname="decision", regression=False, multiClass=False, nClasses=-1, inline=True):
    rtntype = "double"
    if regression: rtntype = "int"
    inline = "inline " if inline else ""
    cout = "template <typename C=std::vector<double>>\n"
    cout += "{}{} {}(const C& args) {{\n".format(inline, rtntype, dtname)
    cout += mkcxxiftree(tree.GetRoot(), 1, regression, multiClass, nClasses)
    cout += "\n}"
    return cout

def dt_to_py(tree, dtname="decision", regression=False, multiClass=False, nClasses=-1):
    cout = "def {}(args):\n".format( dtname)
    cout += mkpyiftree(tree.GetRoot(), 1, regression, multiClass, nClasses)
    return cout

def make_tmvabdt_argparser(LANG="C++ or Python"):
    LANG_human = LANG
    if LANG == "c++":
        LANG_human = "C++"
    elif LANG == "py":
        LANG_human = "Python"

    ap = pc.get_args_parser(desc=["TMVA BDT", f"{LANG_human} code"])
    ap.add_argument("VARIABLES", nargs="?", default=None, help="comma-separated names of input variables")
    ap.add_argument("-r", "--regression", dest="REGRESSION", action="store_true", default=False, help="return values for regression, rather than labels for classification")
    ap.add_argument("--nc", "--nClasses", "--nclasses", dest="NCLASSES", default=-1, type=int, help="if using multiClass option, please specify how many output classes are expected")
    ap.add_argument("--no-inline", dest="INLINE", action="store_false", default=True, help="don't make the DT functions inline for C++")
    ap.add_argument("--write-validation", dest="MAIN", action="store_true", default=False, help="add a main function for trivial testing")
    ap.add_argument("--run-validation", dest="RUNMAIN", default=None,nargs="*", help="run the main function for trivial testing. Optionally supply the BDT inputs.")
    return ap

def main(args, LANG):

    if args.RUNMAIN is not None:
        args.MAIN = True

    # Get the func name, in the event user provided a path
    funcName = os.path.basename(args.NAME) if "/" in args.NAME else args.NAME
    
    try:
        from ROOT import TFile, TTree, TMVA
    except ImportError:
        print("TMVA conversion requires the ROOT Python module to be installed")
        exit(1)

    # No longer have a multiclass argument, rather, if you specificy nclasses > 1
    # then assume its multiclass (as NCLASSES must be supplied)
    MULTICLASS = True if args.NCLASSES > 1 else False
    
    ## Load the BDT into TMVA, using the discovered variables
    TMVA.Tools.Instance()
    reader = TMVA.Reader("!Color:!Silent")
    testinputs = []
    add_variables_to_reader(reader, args)
    reader.BookMVA("MyBDT", args.FILE)
    bdt = reader.FindMVA("MyBDT")

    ## DEBUG PRINTOUTS FOR TREE 1
    # print(bdt, type(bdt), "", sep="\n")
    # t0 = bdt.GetForest()[0]
    # print(t0, type(t0), sep="\n")
    # print()
    # printNodes(t0.GetRoot())
    # print()
    # print(dt_to_cpp(t0))

    ## Generate the set of individual decision trees
    boostweights = bdt.GetBoostWeights()
    couts, treefns = [], []
    for it, tree in enumerate(bdt.GetForest()):
        treefn = "{}_{:03d}".format(funcName, it)
        treefns.append(treefn)
        if LANG == "c++":
            tree = dt_to_cpp(tree, treefn, args.REGRESSION, MULTICLASS, args.NCLASSES, args.INLINE)
        elif LANG == "py":
            tree = dt_to_py(tree, treefn, args.REGRESSION, MULTICLASS, args.NCLASSES)
        couts.append(tree)

    ## Set the language-specific parts, and add top-level functions that sum over tree output-node values
    inline = "inline " if (LANG == "c++" and args.INLINE) else ""
    sumstr = " + ".join("{}*{}(args)".format(w, tf) for (w,tf) in zip(boostweights, treefns))
    multiclasslines=[]
    if MULTICLASS:
        for ic in range(args.NCLASSES):
            thisclasstrees = []
            for it in range(len(treefns)):
                if it % int(args.NCLASSES) == ic :
                    thisclasstrees += [treefns[it]]
            treeSum=" + ".join(["%s(args)"%(tf) for tf in thisclasstrees] )
            vals = "exp(%s)" % (treeSum)
            multiclasslines += [vals]

    cout = ""
    if LANG == "c++":
        ext = ".cc"
        cout += "#include <vector>\n"
        if args.MAIN:
            cout += "#include <iostream>\n"
        if MULTICLASS:
            cout += "#include <math.h>\n"
        cout += "\n"

        if MULTICLASS:
          btree = """\
          template <typename C=std::vector<double>>
          {inline}std::vector<double> {bdtname}(const C& args) {{
            std::vector<double> result;
            std::vector<double> vals = {{ {multiclasslines} }};
            for(int ic = 0; ic < {nclasses}; ic++){{
              double norm = 0.0;
              for( int jc = 0; jc < {nclasses}; jc++){{
                if (ic == jc) continue;
                norm += vals[jc] / vals[ic];
              }}
              result.push_back(1.0 / (1.0 + norm));
            }}
            return result;
          }}
        """.format(inline=inline, bdtname=funcName, nclasses=args.NCLASSES, multiclasslines=", ".join(multiclasslines), scale=1.0)
        else: # vanilla regressions and bdts
          btree = """\
          template <typename C=std::vector<double>>
          {inline}double {bdtname}(const C& args) {{
            return ({sumstr}) / {norm};
          }}""".format(inline=inline, bdtname=funcName, scale=1.0, sumstr=sumstr, norm=sum(boostweights))

    elif LANG == "py":
        ext = ".py"
        cout += "#! /usr/bin/env python\n"
        if args.MAIN:
            cout += "from __future__ import print_function\n"
        if MULTICLASS:
            cout += "from math import exp\n"
        cout += "\n"
        if MULTICLASS:
            btree = """\
          def {bdtname}(args):
            result = []
            vals = [{multiclasslines}]
            for ic in range({nclasses}):
              norm = 0.0
              for jc in range({nclasses}):
                if (ic == jc): continue
                norm += vals[jc] / vals[ic]
              result.append(1.0 / (1.0 + norm))
            return result
          """.format(bdtname=funcName, nclasses=args.NCLASSES, multiclasslines=", ".join(multiclasslines), scale=1.0)
        else: # vanilla regressions and bdts
            btree = """\
          def {bdtname}(args):
            return ({sumstr}) / {norm}
          """.format(bdtname=funcName, scale=1.0, sumstr=sumstr, norm=sum(boostweights))

    couts.append(textwrap.dedent(btree))
    cout += "\n\n".join(couts)


    ## Add a main function for testing (in C++'s case, needed to test compiled-object size)
    if args.MAIN:

        # Check if user specified inputs at the command line
        # N.b. these should have already been loaded in and checked, but because 
        # of ROOT, let's do the check again here for clarity.
        if args.RUNMAIN is None or args.RUNMAIN == []:
            # n.b. if you change this change also in petrifyml_common.py
            # TODO: move here? its a tmvabdt specific function.
            testinputs = list(range(len(args.VARIABLES)))
        else:
            testinputs = [float(f) for f in args.RUNMAIN]
            if len(testinputs) != len(args.VARIABLES):
                raise Exception("Classifier expects {} inputs, you have provided {} test inputs".format(
                    len(args.VARIABLES), len(testinputs)))

        if LANG == "c++":
            cppinputargs = ", ".join(map(str, testinputs))   
            if MULTICLASS:
                mainfn = textwrap.dedent("""\
                int main() {{
                std::vector<double> args({{ {cppinputargs} }});
                std::vector<double> x = {bdtname}(args);
                for (const double d : x){{       
                    std::cout << d << ",";
                }}
                return 0;
                }}
                """.format(cppinputargs=cppinputargs, bdtname=funcName))
            else:
                mainfn = textwrap.dedent("""\
                int main() {{
                std::vector<double> args({{ {cppinputargs} }});
                double x = {bdtname}(args);
                std::cout << x << std::endl;
                return 0;
                }}
                """.format(cppinputargs=cppinputargs, bdtname=funcName))

            print("A main has been added to your cpp file. Compile it with: ")
            print(f"\tg++ {args.NAME}.cc -o {args.NAME}")
            print("And execute with: ")
            executeCommand = args.NAME if args.NAME.startswith("/") else "./"+args.NAME 
            print(f"\t{executeCommand}")

        elif LANG == "py":
            mainfn = textwrap.dedent("""\
            if __name__ == "__main__":
                args = {args}
                x = {bdtname}(args)
                print(x)
            """.format(args=testinputs, bdtname=funcName))

        cout += "\n\n" + mainfn

    ## Output to terminal and file
    if args.VERBOSE:
        print(cout)
    with open(args.NAME + ext, "w") as f:
        f.write(cout)

    if args.RUNMAIN is not None:
        import subprocess
        
        # First evaluate the TMVA score.
        # Note that due to "BDT inputs as pointers _at construction_" insanity
        # the inputs have (hopefully) already been set.
        expectedoutput = np.array(reader.EvaluateMulticlass("MyBDT") if MULTICLASS else reader.EvaluateMVA("MyBDT"))
        print ("    Expected ouput:", expectedoutput)

        if LANG == "py":
            run_command = ["python3", args.NAME+".py"]
            pythonOut = subprocess.run(run_command, check=True, capture_output=True, text=True)
            print("    python output is {}".format(pythonOut.stdout))
            if not MULTICLASS:
                petrifyOut = float(pythonOut.stdout)
                if (np.isclose(petrifyOut, expectedoutput)):
                    print ("BDTs agree! Test passed")
                else:
                    raise Exception("BDTs do not agree! Debugging needed!")
            else:
                import ast
                petrifyOut = ast.literal_eval(pythonOut.stdout)
                if np.isclose(petrifyOut, expectedoutput).all():
                    print ("BDTs agree! Test passed")
                else:
                    raise Exception("BDTs do not agree! Debugging needed!")
        

        elif LANG == "c++":
            compile_command = ["g++", args.NAME+".cc", "-o", args.NAME]
            compile_result = subprocess.run(compile_command, check=True, capture_output=True, text=True)
            if compile_result.returncode != 0:
                raise Exception("Compilation failed with output\n{}".format(compile_result.stderr()))
            print("BDT compiled...")

            execute_result = subprocess.run([executeCommand], capture_output=True, text=True, check=True)
            print("    cpp output is:  {}".format((execute_result.stdout)))

            if not MULTICLASS:    
                if (np.isclose(float(execute_result.stdout), expectedoutput)):
                    print ("BDTs agree! Test passed")
                else:
                    raise Exception("BDTs do not agree! Debugging needed!")
            else:
                import ast
                # Strip out trailing comma, convert to list
                petrifyOut = ast.literal_eval("["+execute_result.stdout[:-1]+"]")
                if np.isclose(petrifyOut, expectedoutput).all():
                    print ("BDTs agree! Test passed")
                else:
                    raise Exception("BDTs do not agree! Debugging needed!")

def main_wrapper(LANG):
    args = make_tmvabdt_argparser(LANG).parse_args()
    main(args, LANG=LANG)

def main_wrapper_cpp():
    main_wrapper(LANG="c++")

def main_wrapper_py():
    main_wrapper(LANG="py")

if __name__ == "__main__":
    main_wrapper_py()
