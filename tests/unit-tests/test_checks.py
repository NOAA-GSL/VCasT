import os
import subprocess
import unittest
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class TestVcastDirectInputs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Define test cases for direct vcast commands and run them.
        """
        cls.test_cases = [
            {
                "input_file": "input_files/HRRR/00/hrrr.2024040103.wrfprsf00.T2M.grib2",
                "command": ["vcast", "input_files/HRRR/00/hrrr.2024040103.wrfprsf00.T2M.grib2"],
                "expected_files": []  # Add expected output file paths here if available.
            },
            {
                "input_file": "input_files/REF/ref_2024040102_f001.nc",
                "command": ["vcast", "input_files/REF/ref_2024040102_f001.nc"],
                "expected_files": []  # Add expected output file paths here if available.
            }
        ]

        # Run each vcast command and log the process.
        for case in cls.test_cases:
            logger.info(f"Running command: {' '.join(case['command'])}")
            try:
                subprocess.run(
                    case["command"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Command succeeded for {case['input_file']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Command failed for {case['input_file']}: {e}")
                raise RuntimeError(f"vcast command failed for {case['input_file']}: {e}")

    def test_commands_run(self):
        """
        Test that each vcast command ran successfully.
        If expected output files are defined, also verify that they exist.
        """
        for case in self.test_cases:
            with self.subTest(input_file=case["input_file"]):
                logger.info(f"Verifying test for {case['input_file']}")
                # If there are expected output files, check they exist.
                for output_file in case["expected_files"]:
                    self.assertTrue(os.path.exists(output_file),
                                    f"Expected output file not found: {output_file}")

    @classmethod
    def tearDownClass(cls):
        """
        Optionally remove generated output files.
        """
        for case in cls.test_cases:
            for output_file in case["expected_files"]:
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                        logger.info(f"Removed file: {output_file}")
                    except Exception as e:
                        logger.error(f"Error removing {output_file}: {e}")

if __name__ == "__main__":
    unittest.main()

