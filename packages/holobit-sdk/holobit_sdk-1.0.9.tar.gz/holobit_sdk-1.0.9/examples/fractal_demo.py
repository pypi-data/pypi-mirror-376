"""Demostración de generación y visualización de fractales."""

from holobit_sdk.visualization.fractal_plot import visualizar_fractal
import numpy as np


def generar_fractal(seed=None, density=0.5, size=50):
    """Genera un fractal simple usando ruido aleatorio."""
    rng = np.random.default_rng(seed)
    datos = rng.random((size, size))
    return (datos < density).astype(float)


if __name__ == "__main__":
    # Construye y grafica dos variaciones del fractal
    fig, axes = visualizar_fractal(
        generar_fractal,
        modo="3D",
        semillas=[42, 123],
        densidades=[0.3, 0.7],
    )

    for ax in axes:
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    import matplotlib.pyplot as plt

    plt.show()
