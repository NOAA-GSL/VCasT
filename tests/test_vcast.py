import os
import subprocess
import yaml
import unittest
import filecmp

class TestVcastExecution(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """
        Load YAML configurations and run vcast commands.
        """
        cls.test_cases = [
            {
                "config": "input_files/hrrr.t00z.wrfprsf00.grib2",
                "expected_files": [],  # No expected output
                "control_files": [],  # No control file
                "command": ["vcast", "input_files/hrrr.t00z.wrfprsf00.grib2"],
            },
            {
                "config": "./configs/config_mvts_t2m.yaml",
                "expected_files": ["graphhrr-T2M.txt"],
                "control_files": ["./control_outputs/graphhrr-T2M.txt"],
                "command": ["vcast", "./configs/config_mvts_t2m.yaml"],
            },
            {
                "config": "./configs/config_conv1.yaml",
                "expected_files": ["test_agg.data"],  # Update expected output filename
                "control_files": ["./control_outputs/test_agg.data"],  # Control file
                "command": ["vcast", "./configs/config_conv1.yaml"],
            },
            {
                "config": "./configs/config_conv2.yaml",
                "expected_files": ["test_agg_all.data"],  # Update expected output filename
                "control_files": ["./control_outputs/test_agg_all.data"],  # Control file
                "command": ["vcast", "./configs/configs_conv2.yaml"],
            },
            {
                "config": "./configs/config_plot.yaml",
                "expected_files": ["GSS_APCP_03.png"],  # Expected plot output
                "control_files": ["./control_outputs/GSS_APCP_03.png"],  # Expected control image
                "command": ["vcast", "./configs/config_plot.yaml"],
            }
        ]

        for test_case in cls.test_cases:
            try:
                subprocess.run(
                    test_case["command"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"vcast command failed for {test_case['config']}: {e}")

            # If YAML-based test, determine expected output paths
            if test_case["config"].endswith(".yaml") and test_case["expected_files"]:
                with open(test_case["config"], "r") as file:
                    config_data = yaml.safe_load(file)
                
                test_case["expected_files"] = [
                    os.path.abspath(os.path.join(config_data.get("output_dir", "."), file))
                    for file in test_case["expected_files"]
                ]

    def test_files_exist(self):
        """
        Ensure all expected output files are created.
        """
        for test_case in self.test_cases:
            if test_case["expected_files"]:  # Skip if no expected files
                for file in test_case["expected_files"]:
                    self.assertTrue(os.path.exists(file), f"Output file not found: {file}")

    def test_files_exist(self):
        """
        Ensure all expected output files are created.
        """
        for test_case in self.test_cases:
            if test_case["expected_files"]:  # Skip if no expected files
                for file in test_case["expected_files"]:
                    self.assertTrue(os.path.exists(file), f"Output file not found: {file}")

    def test_files_not_empty(self):
        """
        Ensure all expected output files are not empty.
        """
        for test_case in self.test_cases:
            if test_case["expected_files"]:  # Skip if no expected files
                for file in test_case["expected_files"]:
                    self.assertTrue(os.path.getsize(file) > 0, f"Output file is empty: {file}")

    def test_output_matches_control_files(self):
        """
        Compare generated output files with corresponding control files.
        """
        for test_case in self.test_cases:
            if test_case["expected_files"] and test_case["control_files"]:  # Skip if no expected files
                for output_file, control_file in zip(test_case["expected_files"], test_case["control_files"]):
                    self.assertTrue(os.path.exists(control_file), f"Control file not found: {control_file}")
                    
                    if output_file.endswith(".png"):  # Special case for image files
                        self.assertTrue(os.path.getsize(output_file) == os.path.getsize(control_file), 
                                        f"Image file {output_file} differs in size from control {control_file}.")
                    else:
                        files_are_identical = filecmp.cmp(output_file, control_file, shallow=False)
                        self.assertTrue(files_are_identical, f"Output file {output_file} does not match control file {control_file}.")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up: Delete the generated output files after tests.
        """
        for test_case in cls.test_cases:
            for file in test_case["expected_files"]:
                if os.path.exists(file):
                    os.remove(file)

if __name__ == "__main__":
    unittest.main()