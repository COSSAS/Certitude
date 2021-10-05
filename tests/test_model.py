import tempfile
from importlib import resources
from pathlib import Path

import certitude.utils.data
from certitude.core.data_model import create_features_dataframe, train_model
from certitude.utils.config import config

config = config()


def test_train() -> None:
    with resources.path(certitude.utils.data, "default_dataset.csv") as path:
        dataset = create_features_dataframe(path, labeled=True)

    temp_model_file = tempfile.NamedTemporaryFile()

    train_model(dataset, config["features"], Path(temp_model_file.name))
