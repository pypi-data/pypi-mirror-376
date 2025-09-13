def load_and_infer_onnx(onnxpath, inputs):
  import onnxruntime as ort

  session = ort.InferenceSession(onnxpath, providers=["CPUExecutionProvider"])
  input_name = session.get_inputs()[0].name
  output_name = session.get_outputs()[0].name

  output = session.run([output_name], {input_name: inputs})[0][0]
  print("Onnx out", output)
  return output