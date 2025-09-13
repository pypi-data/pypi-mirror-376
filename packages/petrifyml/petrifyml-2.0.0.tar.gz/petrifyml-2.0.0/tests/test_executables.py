import os
import pytest
import yaml
from pathlib import Path
import subprocess

def get_cmd_args(cl_args_dict):
    cl_args = [cl_args_dict["command"]]

    # attach args
    if "args" in cl_args_dict:
      for arg in cl_args_dict["args"]:
        cl_args.append(arg)

    # attach options
    if "options" in cl_args_dict:
      for key, option in cl_args_dict["options"].items():
        cl_args.append(f"--{key}")
        if isinstance(option, list):
          for o in option:
            cl_args.append(o)
        else:
          cl_args.append(option)

    # attach switches
    if "switches" in cl_args_dict:
      for switch in cl_args_dict["switches"]:
        cl_args.append(switch)

    # arg parser expects str items
    for i in range(len(cl_args)):
      cl_args[i] = str(cl_args[i])

    return cl_args

def run_cmd(cmd):
  result = subprocess.run(
      cmd,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT
  )
  print(result.stdout)
  return result

def get_arguments_examples():
  THIS_DIR = Path(__file__).parent
  TEST_DATA_DIR = THIS_DIR / "testdata/" # Path to the co-located test data direc

  args_path = TEST_DATA_DIR / "cl_args.yaml"
  with open(args_path, 'r') as f:
    return yaml.load(f, yaml.FullLoader)

def test_executables():
  arguments_examples = get_arguments_examples()

  for key, value in arguments_examples.items():
    if "needs_root" in value and value["needs_root"]:
      continue

    cmd = get_cmd_args(value)
    result = run_cmd(cmd)
    assert result.returncode == 0

@pytest.mark.root_test
def test_root_executables():
  arguments_examples = get_arguments_examples()

  for key, value in arguments_examples.items():
    if not "needs_root" in value or not value["needs_root"]:
      continue

    cmd = get_cmd_args(value)
    result = run_cmd(cmd)
    assert result.returncode == 0