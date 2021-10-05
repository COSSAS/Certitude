import argparse
import sys
from importlib.metadata import metadata
from pathlib import Path
from typing import Dict

import certitude


def parse_arguments() -> Dict:
    package_description = metadata(certitude.__package__)["Summary"]
    package_version = metadata(certitude.__package__)["Version"]
    description = f"""{package_description} - v{package_version}"""

    parser = argparse.ArgumentParser(
        description=description, prog="python -m certitude"
    )

    def existing_path(string) -> Path:
        path = Path(string)
        if path.is_file():
            return path.absolute()
        else:
            parser.error("The provided path does not exist or is not a file.")

    def nonexisting_path(string) -> Path:
        path = Path(string)
        if not path.exists():
            return path.absolute()
        else:
            parser.error("The provided path already exists.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--url", help="A single URL to classify.", type=str)
    group.add_argument(
        "--batch",
        help="A CSV of URLs to classify.",
        type=existing_path,
        metavar=".CSV FILE",
    )
    group.add_argument(
        "--train",
        help="Train a new model. Provide a non-existing path to create the new model file.",
        type=nonexisting_path,
        metavar=".JOBLIB FILE",
    )

    parser.add_argument(
        "-m",
        "--model",
        help="Path to a trained model. Defaults to a built-in sample model.",
        type=existing_path,
        metavar=".JOBLIB FILE",
    )
    parser.add_argument(
        "-d",
        "--dataset",
        help="Path to a CSV dataset you want to train on. Defaults to a built-in sample dataset.",
        type=existing_path,
        metavar=".CSV FILE",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a custom configuration file. If omitted, will use default settings.",
        type=existing_path,
        metavar=".YML FILE",
    )
    parser.add_argument(
        "-v", "--verbose", help="Show debug logging.", action="store_true"
    )
    args = parser.parse_args()
    if not args.url and not args.train and not args.batch:
        parser.print_help()
        sys.exit(2)

    return args
