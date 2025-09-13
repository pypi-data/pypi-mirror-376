from pathlib import Path
from petrifyml.sklbdt_to_cpp import main
from petrifyml.sklbdt_to_cpp import make_sklbdt_to_cpp_argparser

# Get the directory of the current test file
THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = THIS_DIR / "testdata/sklbdt" # Path to the co-located test data direc

def test_sklbdt_to_cpp_job(tmp_path):
    datapath = TEST_DATA_DIR / "sklearn_gb_classifier.job"
    assert datapath.exists(), "Cannot find test data!"
    parser = make_sklbdt_to_cpp_argparser()
    tmp_outputpath = str(tmp_path)+"/decision_example"
    args = parser.parse_args([str(datapath), "-n", tmp_outputpath,
                                "--run-validation",
                                "0.1470137125543316", "-2.158368447357768", "2.8378576940179716","-4.219815916216309","0.29148260177614926"])
    main(args)

def test_sklbdt_to_cpp_pkl(tmp_path):
    datapath = TEST_DATA_DIR / "sklearn_gb_classifier.pkl"
    assert datapath.exists(), "Cannot find test data!"
    parser = make_sklbdt_to_cpp_argparser()
    tmp_outputpath = str(tmp_path)+"/decision_example"
    args = parser.parse_args([str(datapath), "-n", tmp_outputpath,
                                "--run-validation",
                                "0.1470137125543316", "-2.158368447357768", "2.8378576940179716","-4.219815916216309","0.29148260177614926"])
    main(args)
