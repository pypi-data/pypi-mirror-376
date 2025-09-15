import matplotlib.pyplot as plt
from matplotlib import animation

from holobit_sdk.visualization.fractal_plot import (
    visualizar_fractal,
    visualizar_dinamica,
)


def fractal(seed=None, density=0.5, size=10):
    """Generador simple de fractales para pruebas."""
    import numpy as np

    rng = np.random.default_rng(seed)
    datos = rng.random((size, size))
    return (datos < density).astype(float)


def test_visualizar_fractal_retorn_figuras_validas():
    fig, axes = visualizar_fractal(fractal, semillas=[0, 1], densidades=[0.3, 0.6])
    assert isinstance(fig, plt.Figure)
    assert len(axes) == 2
    plt.close(fig)


def test_visualizar_fractal_animado():
    frames = [fractal(seed=i) for i in range(3)]
    fig, ax, anim = visualizar_fractal(frames, modo="animado")
    assert isinstance(anim, animation.FuncAnimation)
    plt.close(fig)


def test_visualizar_dinamica_funcion():
    frames = [fractal(seed=i) for i in range(3)]
    fig, ax, anim = visualizar_dinamica(frames)
    assert isinstance(anim, animation.FuncAnimation)
    plt.close(fig)


def test_visualizar_fractal_proyeccion_dim_mayor():
    import numpy as np

    datos = np.random.random((5, 5, 2, 2))
    fig, axes = visualizar_fractal(datos, modo="2D", proyeccion="mean")
    assert isinstance(fig, plt.Figure)
    assert len(axes) == 1
    plt.close(fig)
