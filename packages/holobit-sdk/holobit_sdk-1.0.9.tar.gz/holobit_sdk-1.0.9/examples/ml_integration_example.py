"""Ejemplo de integración del Holobit SDK con bibliotecas de ML.

Este script muestra cómo convertir datos de ``numpy``/``pandas`` en Holobits y
Holocrones, cómo integrarlo en un pipeline de scikit-learn y cómo iterar con un
``DataLoader`` de PyTorch.
"""

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from holobit_sdk.api import (
    HolobitTransformer,
    holobit_dataloader,
    holocron_from_dataframe,
)

# ---------------------------------------------------------------------------
# Datos de ejemplo
# ---------------------------------------------------------------------------

df = pd.DataFrame(np.arange(24).reshape(2, 12))

# Conversión directa a Holocron
holocron = holocron_from_dataframe(df)
print("Holocron con", len(holocron.holobits), "holobits")

# Uso en un pipeline de scikit-learn
pipeline = Pipeline([("holobits", HolobitTransformer())])
resultado = pipeline.fit_transform(df.values)
print("Pipeline produjo", len(resultado), "holobits")

# Iteración con PyTorch
loader = holobit_dataloader(df.values, batch_size=1, shuffle=False)
for batch in loader:
    print("Batch con", len(batch), "elementos")
