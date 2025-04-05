import os
import unittest
import yaml
import subprocess
import filecmp
import time
import logging

# Configure logging for detailed output during tests.
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class GeneralTestFramework(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load test specification from the YAML file.
        test_yaml = os.path.join(os.path.dirname(__file__), "test_cases.yaml")
        with open(test_yaml, "r") as f:
            cls.test_spec = yaml.safe_load(f)
        logging.info("Loaded test specification from '%s'", test_yaml)

    def run_test_case(self, test_case):
        # Resolve the absolute path to the example directory.
        example_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", test_case["example_dir"]))
        logging.info("Starting test case '%s' in directory '%s'", test_case["name"], example_dir)
        
        # List to collect paths of output files that are created.
        created_files = []
        
        try:
            # Loop through each command defined for this test case.
            for command in test_case["commands"]:
                config_file = command["config"]
                config_path = os.path.join(example_dir, config_file)
                logging.info("Executing command: vcast %s", config_path)
                
                start_time = time.time()
                result = subprocess.run(
                    ["vcast", config_path],
                    cwd=example_dir,
                    capture_output=True,
                    text=True
                )
                elapsed_time = time.time() - start_time
                logging.info("Command completed in %.2f seconds", elapsed_time)
                
                if result.stdout:
                    logging.info("STDOUT: %s", result.stdout.strip())
                if result.stderr:
                    logging.info("STDERR: %s", result.stderr.strip())
                
                self.assertEqual(
                    result.returncode, 0,
                    msg=f"Test case '{test_case['name']}' with config '{config_file}' failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                )
                
                # Compare each output file against its expected file.
                outputs = command.get("outputs", {})
                for output_file, expected_file in outputs.items():
                    output_path = os.path.join(example_dir, output_file)
                    expected_path = os.path.join(example_dir, expected_file)
                    logging.info("Comparing output file '%s' with expected '%s'", output_path, expected_path)
                    
                    self.assertTrue(
                        os.path.exists(output_path),
                        msg=f"Output file '{output_path}' missing in test case '{test_case['name']}'."
                    )
                    files_equal = filecmp.cmp(expected_path, output_path, shallow=False)
                    self.assertTrue(
                        files_equal,
                        msg=f"File '{output_file}' in test case '{test_case['name']}' does not match expected output."
                    )
                    logging.info("File '%s' matches expected output.", output_file)
                    # Record file for removal later.
                    created_files.append(output_path)
        finally:
            # Remove all files that were created in this test case.
            for filepath in created_files:
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logging.info("Removed output file: %s", filepath)
                except Exception as err:
                    logging.error("Failed to remove output file %s: %s", filepath, err)

    def test_all_cases(self):
        # Run each test case from the YAML file as a subTest so all cases are executed.
        for test_case in self.test_spec["tests"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_test_case(test_case)

if __name__ == "__main__":
    unittest.main()
