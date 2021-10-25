import os
import tempfile
from pathlib import Path

from certitude.core.data_model import create_features_dataframe, train_model
from certitude.utils.config import config

config = config()


def test_train() -> None:
    dirname = os.path.dirname(__file__)
    dataset = create_features_dataframe(
        Path(os.path.join(dirname, "data/testset_labeled.csv")), labeled=True
    )

    temp_model_file = tempfile.NamedTemporaryFile()

    train_model(dataset, config["features"], Path(temp_model_file.name))
