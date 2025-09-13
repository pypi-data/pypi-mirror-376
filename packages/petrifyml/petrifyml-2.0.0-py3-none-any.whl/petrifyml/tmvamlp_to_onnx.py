#! /usr/bin/env python3

"""
Translate a TMVA MLP classifier to Keras and then to ONNX

Scikit-learn cannot be used for this because the exported ONNX file can't be validated by reading it in via TMVA SOFIE:
- `skl2onnx` parses the "classes" field as `string` or `int32`
  (https://github.com/onnx/sklearn-onnx/blob/2bd2d8f59160d6acdbdfc5ed12f3f819941e1f78/skl2onnx/operator_converters/multilayer_perceptron.py#L122)
  but TMVA can only handle `int64` and `float` (https://root.cern/doc/v632/RModelParser__ONNX_8cxx_source.html#l00374).
  Therefore it is required to edit `multilayer_perceptron.py` from `skl2onnx` by hand to amend this.
- Something in a scikit-learn MLP is parsed as operator `ArgMax`
  (https://github.com/onnx/sklearn-onnx/blob/2bd2d8f59160d6acdbdfc5ed12f3f819941e1f78/skl2onnx/operator_converters/multilayer_perceptron.py#L192)
  and TMVA does not support `ArgMax`
  (https://github.com/root-project/root/issues/10360, https://root.cern/doc/v632/RModelParser__ONNX_8cxx_source.html#l00089 and 
  https://root.cern/doc/master/RModelParser__ONNX_8cxx_source.html#l00245).
  That is a shame as `ArgMax` is part of ONNX since operator set 1 (https://github.com/onnx/onnx/blob/rel-1.9.1/docs/Operators.md).
  (Choosing a concrete `opset` version does not solve the issue but merely has TMVA complain about being unable to fuse something
  *earlier* in the parsing, starting with version 6. Tested were 1, 2, 3, 5, 6, 8, 10, 14.)
"""

# use factory pattern to allow delaying tf_keras import
def make_ROOTNormalizeTransform_class():
    class ROOTNormalizeTransform(tf_keras.layers.Layer):
        """ Linear transformation layer for normalization
            Inspired by https://github.com/root-project/root/blob/de5fab1649ca92acf463c3d267daff2e0803c8b4/tmva/tmva/src/VariableNormalizeTransform.cxx#L145
        """
        def __init__(self, ranges, dtype=np.float32):
            super().__init__()
            for r in ranges:
                assert len(r)==2, f"Items should be (minimum, maximum) but given was '{r}'"

            ranges = np.array(ranges, dtype=dtype)
            self.offsets = tf.constant(ranges[:,0], dtype=dtype)
            diffs = ranges[:,1]-ranges[:,0]
            scales = 1./diffs
            self.double_scales = tf.constant(scales * 2., dtype=dtype)
            self.ones = tf.ones(len(ranges), dtype=dtype)

        def call(self, inputs):
            return tf.math.multiply( (inputs - self.offsets), self.double_scales) - self.ones
    
    return ROOTNormalizeTransform

def parse_type(type_string):
    #Parse a variable type from a string
    if type_string=="D" or type_string=="F":
        return np.dtype(type_string.lower())

def get_option(dic, xvar, name, cast_type):
    if xvar.get("name")==name:
        value = cast_type(xvar.text)

        # special cases
        if name=="HiddenLayers":
            value = [int(x) for x in value.split(",")] # TMVA actually uses one more neuron than claimed

        # assign
        dic[name] = value

def get_category(xroot, name_category, name_item):
    "Get all items with @name_item in category @name_category from root @xroot"
    return xroot.find(name_category).findall(name_item)

class TmvamlpToOnnxConverter:
    def __init__(self, args):
        print("Initialising.")
        self.verbose = args.VERBOSE
        self.input_file = args.FILE
        self.output_file = args.NAME
        self.test_data = args.TEST_DATA
        self.validation_only = args.VALIDATION_ONLY
        self.random_seed = args.RANDOM_SEED

        self.param_dict = None
        self.X_train = None
        self.models = None

        self.load_imports()

    def load_imports(self):
        # somewhat ugly as the imports are made global
        # but otherwise difficult to support delayed imports (because tensorflow is slow and verbose) as well as petrify-* executable
        global pc
        import petrifyml.petrifyml_common as pc

        global os
        import os
        global ET
        import xml.etree.ElementTree as ET
        try:
            global pd
            import pandas as pd
            global np
            import numpy as np
        except ImportError:
            print("Error: tmvamlp requires numpy and pandas python modules")
            print("Try `pip install petrifyml[tmvamlp]` to automatically install all.")
            exit(1)

        if not self.validation_only: # don't need tf/keras for validation
            try:
                os.environ["TF_USE_LEGACY_KERAS"] = "1" # use legacy keras (pip install tf_keras), see https://github.com/tensorflow/tensorflow/issues/64515#issuecomment-2036195525
                if not self.verbose:
                    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

                global tf
                import tensorflow as tf
                global tf_keras
                import tf_keras
                global tf2onnx
                import tf2onnx # alternative "keras2onnx" is not under active development
            except ImportError:
                print("Error: tmvamlp requires tensorflow, tf_keras and tf2onnx python modules")
                print("Try `pip install petrifyml[tmvamlp]` to automatically install all.")
                exit(1)

    def process_xml(self):
        # have to parse XML because TMVA MLP API doesn't expose hidden layers, weights, etc.
        print("\nProcessing XML.")

        # general params
        self.param_dict = {}
        xroot = ET.parse(self.input_file).getroot()

        method = xroot.get("Method")
        if method=="CrossValidation::MLP":
            print("Error: The cross validation XML file was given. Please convert all folds separately instead.")
            exit(1)

        for xvar in get_category(xroot, "Options", "Option"):
            get_option(self.param_dict, xvar, "NeuronType", str)
            get_option(self.param_dict, xvar, "EstimatorType", str)
            get_option(self.param_dict, xvar, "HiddenLayers", str)
            get_option(self.param_dict, xvar, "LearningRate", float)

        # classes
        classes = [xvar.get("Name") for xvar in get_category(xroot, "Classes", "Class")]
        n_class = len(classes)
        loss = "binary_crossentropy"
        if n_class>2:
            loss = "sparse_categorical_crossentropy"
        self.param_dict["loss"] = loss

        # variables and spectators
        # spectators are only needed for TMVA validation
        for var_category in ["spectator", "variable"]:
            self.param_dict[f"{var_category}s"] = []
            capitalised_category = var_category[0].upper()+var_category[1:]
            if xroot.find(f"{capitalised_category}s") is not None:
                for xvar in get_category(xroot, f"{capitalised_category}s", capitalised_category):
                    var_name = xvar.get("Label")
                    var_type = parse_type(xvar.get("Type"))
                    self.param_dict[f"{var_category}s"].append( (var_name, var_type) )
        self.param_dict["dtype"] = var_type

        # value ranges
        self.param_dict["ranges"] = []
        transformations = get_category(xroot, "Transformations", "Transform")
        assert len(transformations)==1, f"Can currently only handle 1 transformation but number of given transformations was {len(transformations)}"
        range_class = transformations[0].findall("Class")[-1] # TMVA uses only last set of ranges
        xml_ranges = range_class.findall("Ranges")
        assert len(xml_ranges)==1, f"Can only handle 1 set of ranges but number of given sets of ranges were {len(xml_ranges)}"
        for xvar in xml_ranges[0]:
            minimum = xvar.get("Min")
            maximum = xvar.get("Max")
            self.param_dict["ranges"].append( np.array([minimum, maximum], dtype=self.param_dict["dtype"]) )

        # layout
        self.layout = xroot.find("Weights").find("Layout")

        # dummy data
        data = {}
        for var_name, var_type in self.param_dict["variables"]: # initialise with dummy data of correct type and correct length for number of classes
            data[var_name] = np.empty(n_class, dtype=var_type)
        self.param_dict["classes"] = np.empty(n_class, dtype=np.dtype("int64"))
        data["y"] = self.param_dict["classes"]
        df = pd.DataFrame(data=data)

        if self.verbose:
            print(df)
        self.X_train = df.drop("y", axis=1)

    def get_keras_classifier(self):
        print("\nApplying to Keras classifier.")

        # Set keras dtype
        tf_keras.backend.set_floatx(str(self.param_dict["dtype"]))

        # Create the model
        self.models = {}
        for name in ["nominal", "noNorm"]:
            self.models[name] = tf_keras.models.Sequential(name=self.output_file.split(os.path.sep)[-1])

        nn_layers = self.param_dict["HiddenLayers"][:1]+self.param_dict["HiddenLayers"] # first layer is duplicate

        # add linear transformation layer for normalization
        self.models["nominal"].add(make_ROOTNormalizeTransform_class()(self.param_dict["ranges"], dtype=self.param_dict["dtype"]))

        # have to set values before initialisation because model.weights is read-only
        
        for layer_id, tmva_layer in enumerate(self.layout.findall("Layer")):
            # TMVA lists final (empty) neuron as extra layer => skip this layer
            # use "continue" instead of "break" to crash if there's larger layer multiplicity mismatch
            if layer_id==len(nn_layers):
                continue

            neurons = []
            biasses = []

            for neuron_id, neuron in enumerate(tmva_layer.findall("Neuron")):
                neuron_str = neuron.text.strip() # sanitise string

                coeffs = []
                coeffs = np.empty((len(neuron_str.split(" "))), dtype=self.param_dict["dtype"])
                for coeff_id, coeff in enumerate(neuron_str.split(" ")):
                    coeffs[coeff_id] = coeff
                n = tf.stack(coeffs)

                # last TMVA neuron is actually bias: https://root.cern/doc/master/MethodANNBase_8cxx_source.html#l00372
                target = biasses if neuron_id==nn_layers[layer_id] else neurons

                target.append(n)

            init_kernel = tf_keras.initializers.constant(tf.stack(neurons))
            init_bias   = tf_keras.initializers.constant(tf.stack(biasses))

            units = -1
            activation = self.param_dict["NeuronType"]
            if layer_id+1>=len(nn_layers): # last layer gives category
                if self.param_dict["loss"]=="binary_crossentropy":
                    units = 1
                elif self.param_dict["loss"]=="sparse_categorical_crossentropy":
                    units = n_class

                # last output neuron can take different function: https://root.cern/doc/master/MethodANNBase_8cxx_source.html#l00305
                if self.param_dict["EstimatorType"]=="CE":
                    activation = "sigmoid"
                elif self.param_dict["EstimatorType"]=="MSE":
                    activation = "linear"
                else:
                    raise Exception("Unknown estimator type "+self.param_dict["EstimatorType"])
            else:
                units = nn_layers[layer_id+1]

            tf_layer = tf_keras.layers.Dense(units, dtype=self.param_dict["dtype"], activation=activation, trainable=False, kernel_initializer=init_kernel, bias_initializer=init_bias)
            for model in self.models.values():
                model.add(tf_layer)


        # Configure the model and start training
        sgd = tf_keras.optimizers.SGD(learning_rate=self.param_dict["LearningRate"])
        for model in self.models.values():
            model.compile(loss=self.param_dict["loss"], optimizer=sgd, metrics=["accuracy"])
            model.fit(self.X_train.to_numpy(), self.param_dict["classes"], epochs=1, verbose=self.verbose)

        if self.verbose:
            self.models["nominal"].summary()

    def export_to_onnx(self):
        for model_name, model in self.models.items():
            output_name = self.output_file
            if model_name!="nominal":
                output_name += "_"+model_name
            output_name += ".onnx"
            print(f"\nWriting model to {output_name}")
            if model_name=="noNorm":
                print("This model does not normalize the inputs, e.g. for usage with ROOT. You need to manually scale the inputs according to")
                print("\t- the procedure detailed at https://github.com/root-project/root/blob/de5fab1649ca92acf463c3d267daff2e0803c8b4/tmva/tmva/src/VariableNormalizeTransform.cxx#L145")
                print("\t- using the values given at Transformations/Transform/Class/Ranges from the XML file")
            print("\n")

            onx, external_tensor_storage = tf2onnx.convert.from_keras(model)
            with open(output_name, "wb") as f:
                f.write(onx.SerializeToString())

    def run_validation(self):
        print("\nRunning validation.")
        try:
            import ROOT
            import onnx
        except ImportError:
            print("Error: tmvamlp validation requires the ROOT and ONNX python modules.")
            print("Please make sure you have they are available in the runtime.")
            exit(1)
        from array import array

        if self.test_data is None:
            import random
            random.seed(self.random_seed)
            self.test_data = np.zeros(len(self.param_dict["variables"]), dtype=self.param_dict["dtype"])
            for i, (var_name, var_type) in enumerate(self.param_dict["variables"]):
                range_min, range_max = self.param_dict["ranges"][i]
                self.test_data[i] = range_min + random.random()*(range_max-range_min)
        else:
            assert len(self.test_data) == len(self.param_dict["variables"]), f"Length of given test data was {len(self.test_data)} but MLP expects {len(self.param_dict['variables'])} inputs"
            self.test_data = np.array(self.test_data, dtype=self.param_dict["dtype"])

        outputs = {}

        # use XML model in TMVA
        if self.verbose:
            print("\tProcessing XML file in TMVA")
        reader = ROOT.TMVA.Reader()

        # need to explicitly specify spectators and variables
        variables = []
        for i, (var_name, var_type) in enumerate(self.param_dict["variables"]):
            var = array('f', [self.test_data[i]]) # TMVA::Reader::AddVariable can only handle int and float
            reader.AddVariable(var_name, var)
            variables.append(var)
        for var_name, var_type in self.param_dict["spectators"]:
            var = array('f', [0.0]) # TMVA::Reader::AddVariable can only handle int and float
            reader.AddSpectator(var_name, var)

        model_name = "MLP"
        reader.BookMVA(model_name, self.input_file)
        outputs["TMVA XML"] = [[reader.EvaluateMVA(model_name)]]

        # use ONNX model in TMVA
        # would be nice to do but SOFIE doesn't support enough operators in ROOT v.6.32
        # if self.verbose:
        #     print("\tProcessing ONNX in TVMA file")
        # model = ROOT.TMVA.Experimental.RSofieReader(f"{self.output_file}_noNorm.onnx")
        # outputs["TMVA ONNX"] = model.Compute(self.test_data)

        # use ONNX model in ONNX runtime
        if self.verbose:
            print("\tProcessing ONNX file in ONNX runtime")
        import onnxruntime as ort
        ort_sess = ort.InferenceSession(f"{self.output_file}.onnx")
        test_data_ONNX = np.array((self.test_data,), dtype=self.param_dict["dtype"]) # input expects to read batch size and actual input data
        outputs["ONNX runtime"] = ort_sess.run(None, {"root_normalize_transform_input": test_data_ONNX})[0]

        # use Keras model
        if not self.validation_only: # not available if only running validation
            if self.verbose:
                print("\tProcessing Keras model")
            outputs["Keras model"] = self.models["nominal"].predict(test_data_ONNX, verbose=self.verbose)

        # actual validation
        if self.verbose:
            print(f"\tOutputs: {outputs}")
        first_key, first_output = list(outputs.items())[0]
        for output_key, output_value in outputs.items():
            if output_key == first_key: # trivially correct
                continue

            print(f"Validating '{first_key}' against '{output_key}'.")
            np.testing.assert_almost_equal(first_output, output_value, verbose=self.verbose)

        print("Validation successful.")

def get_tmvamlp_argparser():
    import petrifyml.petrifyml_common as pc
    ap = pc.get_args_parser(desc=["TMVA MLP", "ONNX"])
    ap.add_argument("--run-validation", dest="RUN_VALIDATION", action="store_true", help="Validate the ONNX model against the original model. Requires ROOT.")
    ap.add_argument("--validation-only", dest="VALIDATION_ONLY", action="store_true", help="Only run the validation, do not output ONNX file")
    ap.add_argument("--test-data", dest="TEST_DATA", default=None, nargs="+", help="Test input data to validate generated ONNX model on. If not given, the input is generated from random uniform distributions within the allowed parameter ranges.")
    ap.add_argument("--seed", dest="RANDOM_SEED", default=0, type=int, help="The random seed to use for test input data generation.")

    return ap

def main(args):
    if args.VALIDATION_ONLY:
        args.RUN_VALIDATION = True

    # notify about conflicting options if verbose
    if args.VERBOSE:
        if not args.RUN_VALIDATION:
            if args.TEST_DATA:
                print("WARNING: Test data will be ignored because validation is not run.")
            if args.RANDOM_SEED:
                print("WARNING: Random seed will be ignored because validation is not run.")

        else:
            if args.TEST_DATA and args.RANDOM_SEED:
                print("WARNING: Random seed will be ignored because test data was given.")

    converter = TmvamlpToOnnxConverter(args)
    converter.process_xml()
    if not args.VALIDATION_ONLY:
        converter.get_keras_classifier()
        converter.export_to_onnx()
    if args.RUN_VALIDATION:
        converter.run_validation()

def main_wrapper():
    main(get_tmvamlp_argparser().parse_args())

if __name__ == "__main__":
    main_wrapper()
