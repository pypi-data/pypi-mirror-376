#! /usr/bin/env python3

"""
Translate an lwtnn `lwt::LightweightNeuralNetwork` json file into an onnx file.

This does NOT work on lwt::LightweightGraph networks. They use a different json
schema and so a different conversion script will be needed.

For the moment, only a subset of the lwtnn activation/layer types are supported.
Please feel free to request any layers/activations that are urgently needed
(or better yet, add them yourselves)

The script uses onnx.helper to construct the onnx model graph directly (no
intermediate formats/codes are used).

Requires the onnx, json and numpy python modules. Does not require lwtnn to be
installed, though it is always good practice to run validation yourself.
"""

import json
try:
    import onnx
    from onnx import helper
    from onnx import TensorProto
    import numpy as np
except:
    print("Error: Converting LWTNN networks requires onnx and numpy python modules")
    print("Try `pip install petrifyml[lwtnn]` to automatically install all.")
    exit(1)


class LwtnnToOnnxConverter:
    def __init__(self, name, float_type=TensorProto.FLOAT):
        self.name = name
        self.float_type = float_type
        self.nodes = []
        self.initializers = []
        self.current_input_name = None
        self.input_shape = None
        self.output_shape = None
        self.input_names = None
        self.output_names = None
        self.input_scales = None
        self.input_offsets =None
        self.model_built = False
        self.inputfile = None


    def add_activation(self, activation, layer_name: str):
        # Simpler (no arg) activations
        if activation == "rectified":
            relu_node = helper.make_node('Relu', [self.current_input_name], [f"{layer_name}_relu"], name=f"{layer_name}_relu")
            self.nodes.append(relu_node)
            self.current_input_name = f"{layer_name}_relu"
            return
        elif activation == "softmax":
            softmax_node = helper.make_node('Softmax', [self.current_input_name], [f"{layer_name}_softmax"], name=f"{layer_name}_softmax")
            self.nodes.append(softmax_node)
            self.current_input_name = f"{layer_name}_softmax"
            return
        elif activation == "tanh":
            tanh_node = helper.make_node('Tanh', [self.current_input_name], [f"{layer_name}_tanh"], name=f"{layer_name}_tanh")
            self.nodes.append(tanh_node)
            self.current_input_name = f"{layer_name}_tanh"
            return
        elif activation == "sigmoid":
            sigmoid_node = helper.make_node('Sigmoid', [self.current_input_name], [f"{layer_name}_sigmoid"], name=f"{layer_name}_sigmoid")
            self.nodes.append(sigmoid_node)
            self.current_input_name = f"{layer_name}_sigmoid"
            return

        # More complex activations -- require arguments, acttivation argument no longer a string
        try:
            funcname = activation["function"]
            
            if funcname == "elu":
                if "alpha" not in activation.keys():
                    print("Error: Elu activation must specify an alpha!")
                    exit(1)
            
                elu_node = helper.make_node('Elu', [self.current_input_name], [f"{layer_name}_elu"], alpha=activation["alpha"],name=f"{layer_name}_elu")
                self.nodes.append(elu_node)
                self.current_input_name = f"{layer_name}_elu"
                return
        except:
            pass
    
        print("Error: Unknown activation function {}\n(if you need it, consider adding it yourself!)".format(activation))
        exit(1)


    def convert_dense(self, layer_data, layer_index):
        layer_name = f"dense_{layer_index}"  # Generate a name
        activation = layer_data.get("activation")
        bias = layer_data.get("bias")
        weights = layer_data.get("weights")

        if weights is not None and bias is not None:
            num_outputs = len(bias)
            num_inputs = len(weights) // num_outputs

            #TODO: reshaping then flattening is probably silly, but get everything working first.
            weight_data = np.array(weights).astype(np.float32).reshape(num_outputs, num_inputs).T
            bias_data = np.array(bias).astype(np.float32)

            weight_name = f"{layer_name}_weight"
            bias_name = f"{layer_name}_bias"
            output_name = f"{layer_name}_output"

            self.initializers.append(helper.make_tensor(weight_name, self.float_type, weight_data.shape, weight_data.flatten()))
            self.initializers.append(helper.make_tensor(bias_name, self.float_type, bias_data.shape, bias_data.flatten()))

            self.nodes.append(helper.make_node('Gemm', [self.current_input_name, weight_name, bias_name], [output_name], name=layer_name, transA=0, transB=0))
            self.current_input_name = output_name

            self.add_activation(activation, layer_name)
        else:
            print(f"Error: layer {layer_index} missing weights or bias.")
            exit(1)


    def convert_normalization(self, layer_data, layer_index):
        layer_name = f"normalization_{layer_index}"
        bias = layer_data.get("bias")
        weights = layer_data.get("weights")

        if weights is not None and bias is not None:
            weight_data = np.array(weights).astype(np.float32)
            bias_data = np.array(bias).astype(np.float32)

            scale_name = f"{layer_name}_scale"
            bias_norm_name = f"{layer_name}_bias"
            output_name = f"{layer_name}_output"

            # Assuming this is a form of affine transformation after normalization
            self.initializers.append(helper.make_tensor(scale_name, self.float_type, weight_data.shape, weight_data.flatten()))
            self.initializers.append(helper.make_tensor(bias_norm_name, self.float_type, bias_data.shape, bias_data.flatten()))

            self.nodes.append(helper.make_node('Add', [self.current_input_name, bias_norm_name], [f"{layer_name}_biased"], name=f"{layer_name}_biased"))
            self.nodes.append(helper.make_node('Mul', [f"{layer_name}_biased", scale_name], [output_name], name=layer_name))
        
            self.current_input_name = output_name
        else:
            print(f"Error: layer {layer_index} missing weights or bias.")
            exit(1)


    def convert_layer(self, layer_data, layer_index):
        architecture = layer_data.get("architecture")
        if architecture == "dense":
            self.convert_dense(layer_data, layer_index)
        elif architecture == "normalization":
            self.convert_normalization(layer_data, layer_index)
        else:
            print(f"Error: unsupported architecture: {architecture} at layer {layer_index}.")
            exit(1)


    def lwtnn_to_onnx(self, lwtnn_json_file, onnx_output_file=None,
                      opset=None, ir_ver=None):
        if (lwtnn_json_file is None):
            print("Error: you must provide an input file.")
            exit(1)
        self.inputfile = lwtnn_json_file
        if onnx_output_file == None:
            onnx_output_file = self.name+".onnx"
    
        try:
            with open(lwtnn_json_file, 'r') as f:
                lwtnn_config = json.load(f)
        except:
            print(f"Error opening lwtnn json file '{lwtnn_json_file}'.")
            exit(1)

        inputs_config = lwtnn_config.get("inputs", [])
        layers_config = lwtnn_config.get("layers", [])
        outputs_config = lwtnn_config.get("outputs", [])

        if not inputs_config or not layers_config or not outputs_config:
            print("Error: Missing inputs, layers, or outputs configuration in lwtnn JSON.")
            print(" (is it possible you are trying to convert an lwt::LightweightGraph?)")
            exit(1)

        self.input_names = [input_data["name"] for input_data in inputs_config]
        self.output_names = [output_data for output_data in outputs_config]

        self.input_shape = (None, len(self.input_names))
        self.output_shape = (None,  len(self.output_names))

        # For cleanliness, deal with only input tensor here.
        # Output tensor will be dealt with at the very end.
        input_tensor_info = helper.make_tensor_value_info("input", self.float_type, self.input_shape)
        self.current_input_name="input"

        # Deal with normalisation
        self.input_offsets = np.array([i["offset"] for i in inputs_config])
        self.input_scales = np.array([i["scale"] for i in inputs_config])
        self.initializers.append(helper.make_tensor("offset_input", self.float_type, self.input_offsets.shape, self.input_offsets.flatten()))
        self.initializers.append(helper.make_tensor("scale_input", self.float_type, self.input_scales.shape, self.input_scales.flatten()))
        offset_node = helper.make_node("Add", ["input", "offset_input"], ["offset_output"], name="input_offset_layer")
        scale_node = helper.make_node("Mul", ["offset_output", "scale_input"], ["scale_output"], name="input_scale_layer")
        self.nodes.append(offset_node)
        self.nodes.append(scale_node)
        self.current_input_name="scale_output"

        for i, layer_data in enumerate(layers_config):
            self.convert_layer(layer_data, i)

        output_tensor_info = helper.make_tensor_value_info(self.current_input_name, self.float_type, self.output_shape)

        # Create the graph
        graph = helper.make_graph(
            self.nodes,
            "lwtnn_to_onnx_graph",
            [input_tensor_info],
            [output_tensor_info],
            initializer=self.initializers
        )

        # Create the model
        if ir_ver is not None:
            model = helper.make_model(graph,
                                    producer_name='lwtnn_to_onnx_converter',
                                    opset_imports=opset,
                                    ir_version=ir_ver)
        else:
            model = helper.make_model(graph,
                                    producer_name='lwtnn_to_onnx_converter',
                                    opset_imports=opset)

        # Save the ONNX model
        onnx.save(model, onnx_output_file)

        print(f"Successfully converted lwtnn JSON to ONNX: {onnx_output_file}")
        self.model_built = True
        return model


    def write_validation_model(self):
        if not self.model_built:
            print("Warning: you can't write a validation script until the model has been converted.")
            return
        if (self.float_type == TensorProto.FLOAT16):
            print("Warning: writing validation file not supported for 16-bit floats")
            return
        cpp_ftype = "float" if self.float_type == TensorProto.FLOAT else "double"
        headerstring = """#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <string>
#include "lwtnn/LightweightNeuralNetwork.hh"
#include "lwtnn/parse_json.hh"

#include <onnxruntime_cxx_api.h>
using namespace std;
int main() {
"""
        # Generate some random inputs. As we have means/scales, exploit these
        # to make out random input look more "real"
        # This does not _guaruntee_ that positive definite vars will stay positive,
        # but this should be ok for NNs.
        test_inputs = np.random.normal(loc=-self.input_offsets, scale=1/self.input_scales)

        # Set up inputs
        onnx_input = "\tstd::vector<{}> inputONNX{{{}}};\n".format(cpp_ftype, ", ".join(map(str, test_inputs)))
        lwtnn_input = "\tstd::map<string, double> inputLWTNN{{{}}};\n".format(", ".join([f"{{\"{key}\", {value}}}" for key, value in zip(self.input_names, test_inputs)]))
        onnx_shape = f"\tstd::vector<int64_t> onnx_in_shape = {{1, {self.input_shape[1]}}};\n"
        outkeys = "\tstd::vector<string> outkeys{{{}}};\n".format(", ".join(map(str, [f"\"{k}\""for k in self.output_names])))

        # LWTNN inference.
        lwtnn_infer = """\n// Run lwtnn inference
    std::ifstream i_lwtnn("{}");
    lwt::JSONConfig config_lwtnn = lwt::parse_json(i_lwtnn);
    i_lwtnn.close();
    lwt::LightweightNeuralNetwork network_lwtnn(config_lwtnn.inputs, config_lwtnn.layers, config_lwtnn.outputs);
    std::map<string, double> lwtnn_output = network_lwtnn.compute(inputLWTNN);
""".format(self.inputfile)

        # Run ONNX inference
        onnx_infer = """\n
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "my-app");
    Ort::SessionOptions session_options;
    session_options.SetIntraOpNumThreads(1);
    session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_BASIC);

    // Load model
    Ort::Session session(env, "{}", session_options);
    // Get input and output names
    Ort::AllocatorWithDefaultOptions allocator;

    std::vector<std::string> input_names = session.GetInputNames();
    std::vector<std::string> output_names = session.GetOutputNames();
    const char* input_name = input_names[0].c_str();
    const char* output_name = output_names[0].c_str();

    Ort::TypeInfo type_info = session.GetInputTypeInfo(0);
    auto tensor_info = type_info.GetTensorTypeAndShapeInfo();
    std::vector<int64_t> input_dims = tensor_info.GetShape();
    size_t n_features = input_dims[1];  // assuming shape is [1, n_features]
    std::vector<const char*> input_names_onnx = {{input_name}};
    std::vector<const char*> output_names_onnx = {{output_name}};

    Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value input_tensor = Ort::Value::CreateTensor<{}>(
        memory_info, inputONNX.data(), inputONNX.size(), onnx_in_shape.data(), onnx_in_shape.size());
    std::vector<Ort::Value> output_tensor_onnx = session.Run(Ort::RunOptions{{nullptr}}, &input_name, &input_tensor, 1, &output_name, 1);
    {}* onnx_output_ptr = output_tensor_onnx.front().GetTensorMutableData<{}>();

""".format(self.name+".onnx", cpp_ftype, cpp_ftype, cpp_ftype)

        comparestring = f"""\t// Compare lwtnn/onnx
    const auto crudeFuzzyEquals = [](double A, {cpp_ftype} B){{
        // Cover the zero case
        if (abs(A) < __FLT_EPSILON__ && abs(B) < __FLT_EPSILON__) return true;
        if (A*1.00001 > B && B*1.00001 > A) return true;
        return false;
    }};
    bool allmatch = true;
    for (size_t i = 0; i < outkeys.size(); ++i){{
        if (!(crudeFuzzyEquals(lwtnn_output[outkeys[i]], *(onnx_output_ptr+i)))){{
            std::cout << "Output " << outkeys[i] << " (" << i << ") does not match!\\n";
            std::cout << "LWTNN: " << lwtnn_output[outkeys[i]] << ", ONNX: " << *(onnx_output_ptr+i) << std::endl;
            allmatch = false;
        }}
        else {{
            std::cout << "Output " << outkeys[i] << " (" << i << ") matches!\\n";
            std::cout << "\\tLWTNN: " << lwtnn_output[outkeys[i]] << ", onnxrt: " << *(onnx_output_ptr+i) << std::endl;
        }}
    }}
    if (allmatch){{
        std::cout << "\\n\\nAll outputs within 0.001%. Success!\\n";
    }}
        """

        filestring = (headerstring+
                      lwtnn_input+onnx_input+onnx_shape+outkeys
                      +lwtnn_infer+onnx_infer + comparestring+"\n}")
        with open("validator.cpp", "w") as f:
            f.write(filestring)

        print("Written validation test to validator.cpp")
        print("Compile it with:")
        print("\tg++ validator.cpp -o validator -I/path/to/onnx/include -I/path/to/lwtnn/include -L/path/to/ONNX/lib -L/path/to/lwtnn/lib -lonnxruntime -llwtnn")
        print("Ensure that your LD_LIBRARY_PATH (or equivalent) is correctly set when executing")

def make_lightweightnn_argparser():
    from . import petrifyml_common as pc
    from .onnx_common_utils import add_onnx_argparse_options

    # TODO: I use -n for the output, it is a little misleading in this context...
    ap = pc.get_args_parser(desc=["LightweightNN", "ONNX"])
    add_onnx_argparse_options(ap)
    ap.add_argument("--write-validation", dest="WRITE_VALIDATION", action="store_true",
                    help="Write an example validation code in C++ (lwtnn has no python interface)")
    return ap

def get_lightweightnn_args():
    ap = make_lightweightnn_argparser()
    # Special catcher in case --run-validation is given (not provided)
    _args, unused =  ap.parse_known_args()
    for flag in unused:
        if flag == "--run-validation":
            ap.error("'--run-validation is not supported for lwtnn.\nUse --write-validation and follow the compilation instructions.")
    return ap.parse_args()


def main(args):
    from .onnx_common_utils import get_onnx_float_type, make_opset_info
    print("Initialising...")
    converter = LwtnnToOnnxConverter(args.NAME, get_onnx_float_type(args.FLOAT_TYPE))
    model = converter.lwtnn_to_onnx(args.FILE, ir_ver=args.IR_VER, opset=make_opset_info(args.OPSET_VER))

    if args.WRITE_VALIDATION:
        converter.write_validation_model()

    if (args.TEXT_ONNX):
        with open(args.NAME+".text.onnx", "w") as f:
            f.write(onnx.printer.to_text(model))
        print(f"Written text protobuf of onnx file to {args.NAME}.text.onnx")

# Annoyingly hard to please both pytest and toml script.
def main_wrapper():
    main(get_lightweightnn_args())

if __name__ == "__main__":
    main_wrapper()
