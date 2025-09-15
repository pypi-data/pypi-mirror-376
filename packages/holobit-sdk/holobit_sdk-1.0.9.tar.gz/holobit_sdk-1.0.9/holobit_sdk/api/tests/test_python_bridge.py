import numpy as np
import pandas as pd
import pytest

from holobit_sdk.api import (
    HolobitDataset,
    HolobitTransformer,
    holobit_dataloader,
    holobits_from_dataframe,
    holobits_from_ndarray,
    holocron_from_dataframe,
    holocron_from_ndarray,
)


def _sample_array():
    return np.arange(24).reshape(2, 12)


def test_holobits_from_ndarray():
    arr = _sample_array()
    holobits = holobits_from_ndarray(arr)
    assert len(holobits) == 2
    assert holobits[0].quarks[0].posicion[0] == 0


def test_holocron_from_dataframe():
    df = pd.DataFrame(_sample_array())
    holocron = holocron_from_dataframe(df)
    assert len(holocron.holobits) == 2


def test_sklearn_wrapper():
    arr = _sample_array()
    transformer = HolobitTransformer()
    transformed = transformer.fit_transform(arr)
    assert len(transformed) == 2


def test_torch_dataloader():
    arr = _sample_array()
    loader = holobit_dataloader(arr, batch_size=1, shuffle=False)
    batches = list(loader)
    assert len(batches) == 2
    assert isinstance(batches[0][0], type(batches[0][0]))


def test_dataset_len_and_getitem():
    arr = _sample_array()
    dataset = HolobitDataset(arr)
    assert len(dataset) == 2
    assert dataset[1].quarks[0].posicion[0] == 12
