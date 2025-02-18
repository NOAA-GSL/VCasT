import os
import glob
import subprocess
import yaml
import unittest
import filecmp
import logging

# Configure logging for detailed output.
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class TestVcastConvConfigs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Discover all config_conv_*.yaml files, run vcast for each,
        and record the expected and control output file paths.
        """
        cls.test_cases = []
        # Discover all configuration files matching the pattern.
        config_files = glob.glob("configs/config_conv_*.yaml")
        logger.info(f"Found {len(config_files)} config_conv YAML files.")

        cls.test_cases = []
        for config_file in config_files:
            logger.info(f"Processing conv config: {config_file}")
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)
            # Build a list of expected output files based on keys.
            expected_files = []
            output_keys = ["output_reformat_file", "output_plot_file", "output_agg_file"]
            for key in output_keys:
                if key in config_data:
                    # Assume the path is relative to the project root.
                    rel_path = config_data[key]
                    abs_path = os.path.abspath(os.path.join(rel_path))
                    expected_files.append(abs_path)
                else:
                    logger.warning(f"Key '{key}' not found in {config_file}.")
            # Assume corresponding control files reside in control_outputs.
            control_files = [
                os.path.abspath(os.path.join("control_outputs", os.path.basename(f)))
                for f in expected_files
            ]
            test_case = {
                "config": config_file,
                "expected_files": expected_files,
                "control_files": control_files,
                "command": ["vcast", config_file]
            }
            cls.test_cases.append(test_case)

        # Run the vcast command for each conv configuration.
        for test_case in cls.test_cases:
            logger.info(f"Running command: {' '.join(test_case['command'])}")
            try:
                subprocess.run(
                    test_case["command"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"vcast succeeded for {test_case['config']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"vcast command failed for {test_case['config']}: {e}")
                raise RuntimeError(f"vcast command failed for {test_case['config']}: {e}")

    def test_files_exist(self):
        """
        Verify that each expected output file is created.
        """
        for test_case in self.test_cases:
            for output_file in test_case["expected_files"]:
                with self.subTest(config=test_case["config"], output_file=output_file):
                    logger.info(f"Checking existence of: {output_file}")
                    self.assertTrue(os.path.exists(output_file),
                                    f"Output file not found: {output_file}")

    def test_files_not_empty(self):
        """
        Verify that each expected output file is not empty.
        """
        for test_case in self.test_cases:
            for output_file in test_case["expected_files"]:
                with self.subTest(config=test_case["config"], output_file=output_file):
                    size = os.path.getsize(output_file)
                    logger.info(f"File {output_file} size: {size} bytes")
                    self.assertTrue(size > 0,
                                    f"Output file is empty: {output_file}")

    def test_output_matches_control_files(self):
        """
        Compare each generated output file with its corresponding control file.
        """
        for test_case in self.test_cases:
            if test_case["expected_files"] and test_case["control_files"]:
                for output_file, control_file in zip(test_case["expected_files"], test_case["control_files"]):
                    with self.subTest(config=test_case["config"], output_file=output_file):
                        logger.info(f"Comparing {output_file} to control {control_file}")
                        self.assertTrue(os.path.exists(control_file),
                                        f"Control file not found: {control_file}")
                        identical = filecmp.cmp(output_file, control_file, shallow=False)
                        self.assertTrue(identical,
                                        f"Output file {output_file} does not match control file {control_file}")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up: Delete the generated output files after tests.
        """
        for test_case in cls.test_cases:
            for output_file in test_case["expected_files"]:
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                        logger.info(f"Removed file: {output_file}")
                    except Exception as e:
                        logger.error(f"Error removing {output_file}: {e}")

if __name__ == "__main__":
    unittest.main()

