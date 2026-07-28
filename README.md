# VCasT: Verification and Forecast Evaluation Tool

[![Apache License 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

VCasT (Verification and Forecast Evaluation Tool) is a library designed for weather model verification.

📚 **Documentation:** [https://vcast.readthedocs.io](https://vcast.readthedocs.io)

## Installation

VCasT requires Python 3.10+. Install the full feature set, or a lighter subset via extras:

```bash
# Full install (stats, aggregation, plotting, preprocessing, parallel processing)
pip install ".[all]"

# Lite install (plotting, met-stat, aggregation only)
pip install ".[lite]"

# Add pytest/Pillow for running the test suite
pip install ".[all,dev]"
```

## Usage

VCasT installs a `vcast` console script. Point it at a YAML config file; the
action to run (convert, plot, stats, aggregate, or significance) is inferred
from the config file's contents:

```bash
vcast config.yaml
```

See the [documentation](https://vcast.readthedocs.io) for configuration examples and use cases.

## License

The Apache license will be in effect unless superseded by an existing license in specific files – see the [LICENSE](LICENSE) file for details.