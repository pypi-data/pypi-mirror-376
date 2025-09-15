"""Puente de interoperabilidad con bibliotecas de Python.

Este módulo proporciona funciones utilitarias para convertir estructuras de
``numpy`` y ``pandas`` en objetos nativos del Holobit SDK. Además incluye
wrappers sencillos para integrar estas funciones dentro de pipelines de
scikit-learn y flujos de datos de PyTorch.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core.quark import Quark
from holobit_sdk.quantum_holocron.core.holocron import Holocron

try:  # pragma: no cover - dependencia opcional
    from sklearn.base import BaseEstimator, TransformerMixin
except Exception:  # pragma: no cover
    BaseEstimator = object  # type: ignore

    class TransformerMixin:  # type: ignore
        pass

try:  # pragma: no cover - dependencia opcional
    import torch
    from torch.utils.data import DataLoader, Dataset
except Exception:  # pragma: no cover
    torch = None
    DataLoader = Dataset = object  # type: ignore


# ---------------------------------------------------------------------------
# Conversión de estructuras de datos a Holobits y Holocrones
# ---------------------------------------------------------------------------

def _vector_a_holobit(vector: Sequence[float]) -> Holobit:
    """Convierte un vector numérico en un ``Holobit``.

    Se toman los primeros 6 valores para los quarks y los siguientes 6 para
    los antiquarks. En caso de faltar valores se rellenan con ceros.
    """

    data = list(map(float, vector))
    data.extend([0.0] * (12 - len(data)))
    quarks = [Quark(v) for v in data[:6]]
    antiquarks = [Quark(v) for v in data[6:12]]
    return Holobit(quarks, antiquarks)


def holobits_from_ndarray(arr: np.ndarray) -> List[Holobit]:
    """Genera una lista de ``Holobit`` a partir de un ``ndarray``."""

    arr = np.asarray(arr)
    return [_vector_a_holobit(row) for row in arr]


def holobits_from_dataframe(df: pd.DataFrame) -> List[Holobit]:
    """Genera ``Holobit`` a partir de un ``DataFrame`` de ``pandas``."""

    return holobits_from_ndarray(df.to_numpy())


def holocron_from_ndarray(arr: np.ndarray, ids: Optional[Iterable[str]] = None) -> Holocron:
    """Crea un ``Holocron`` a partir de un ``ndarray``."""

    holocron = Holocron()
    holobits = holobits_from_ndarray(arr)
    ids = list(ids) if ids is not None else [f"h{i}" for i in range(len(holobits))]
    for hid, hb in zip(ids, holobits):
        holocron.add_holobit(hid, hb)
    return holocron


def holocron_from_dataframe(df: pd.DataFrame, ids: Optional[Iterable[str]] = None) -> Holocron:
    """Crea un ``Holocron`` a partir de un ``DataFrame``."""

    return holocron_from_ndarray(df.to_numpy(), ids=ids)


# ---------------------------------------------------------------------------
# Integración con scikit-learn
# ---------------------------------------------------------------------------

class HolobitTransformer(BaseEstimator, TransformerMixin):
    """Transformador compatible con pipelines de scikit-learn."""

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None):  # pragma: no cover - API estándar
        self.holobits_ = holobits_from_ndarray(X)
        return self

    def transform(self, X: np.ndarray) -> List[Holobit]:
        return holobits_from_ndarray(X)


# ---------------------------------------------------------------------------
# Integración con PyTorch
# ---------------------------------------------------------------------------

class HolobitDataset(Dataset):  # type: ignore[misc]
    """Dataset de PyTorch que envuelve una colección de ``Holobit``."""

    def __init__(self, data: np.ndarray | pd.DataFrame):
        if isinstance(data, pd.DataFrame):
            data = data.to_numpy()
        self.holobits = holobits_from_ndarray(data)

    def __len__(self) -> int:
        return len(self.holobits)

    def __getitem__(self, idx: int) -> Holobit:
        return self.holobits[idx]


def holobit_dataloader(
    data: np.ndarray | pd.DataFrame,
    batch_size: int = 32,
    shuffle: bool = True,
    **kwargs,
) -> DataLoader:  # type: ignore[misc]
    """Crea un ``DataLoader`` para iterar sobre ``Holobit``."""

    dataset = HolobitDataset(data)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, collate_fn=kwargs.pop('collate_fn', lambda x: x), **kwargs)
