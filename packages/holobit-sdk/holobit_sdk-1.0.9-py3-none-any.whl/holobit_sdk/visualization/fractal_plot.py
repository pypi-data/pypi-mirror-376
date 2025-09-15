"""Utilidades de visualización de fractales."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def _preprocesar_datos(data, cortes=None, proyeccion="mean"):
    """Aplica cortes o proyecciones a matrices de más de 3 dimensiones.

    Parameters
    ----------
    data:
        Arreglo ``numpy`` que representa el fractal.
    cortes:
        Diccionario ``{eje: indice}`` que indica los cortes a aplicar sobre
        los ejes superiores al segundo.
    proyeccion:
        Modo de proyección a utilizar cuando aún quedan ejes extra. Puede ser
        ``"mean"`` o ``"sum"`` o una función que acepte los parámetros de
        ``numpy``.
    """

    data = np.asarray(data)
    cortes = cortes or {}

    # Aplicar cortes específicos
    for eje, indice in sorted(cortes.items()):
        if eje < data.ndim:
            data = np.take(data, indice, axis=eje)

    # Si aún existen más de 2 dimensiones, proyectar
    if data.ndim > 2:
        eje_extra = tuple(range(2, data.ndim))
        if isinstance(proyeccion, str):
            if proyeccion == "mean":
                data = data.mean(axis=eje_extra)
            elif proyeccion == "sum":
                data = data.sum(axis=eje_extra)
            else:
                raise ValueError(f"Proyección desconocida: {proyeccion}")
        else:
            data = proyeccion(data, axis=eje_extra)

    return data


def visualizar_fractal(
    fractal,
    modo="3D",
    semillas=None,
    densidades=None,
    cortes=None,
    proyeccion="mean",
):
    """Visualiza uno o varios fractales.

    La función acepta un generador de fractales o una matriz ya calculada.
    Cuando se proporcionan ``semillas`` o ``densidades`` se crean variaciones
    del fractal y se muestran todas en la misma figura.

    Args:
        fractal:
            ``callable`` que genera un arreglo 2D o un ``ndarray`` ya calculado.
            En modo ``"animado"`` debe ser una secuencia de matrices.
        modo:
            ``"3D"`` para superficies, ``"2D"`` para imágenes o ``"animado"``
            para generar una animación.
        semillas: Lista de semillas opcionales.
        densidades: Lista de densidades opcionales.
        cortes:
            Diccionario de cortes a aplicar si el fractal posee dimensiones
            superiores.
        proyeccion:
            Método de proyección para dimensiones extra. Acepta ``"mean"``,
            ``"sum"`` o una función ``numpy`` compatible.

    Returns:
        tuple: ``(fig, axes)`` con la figura y los ejes generados.
    """
    if modo == "animado":
        # El parámetro ``fractal`` es una secuencia de matrices ya generadas
        if callable(fractal):
            frames = [np.asarray(f) for f in fractal()]
        else:
            frames = [np.asarray(f) for f in fractal]
        frames = [_preprocesar_datos(f, cortes, proyeccion) for f in frames]
        return visualizar_dinamica(frames)

    semillas = semillas or [None]
    densidades = densidades or [None]
    n = max(len(semillas), len(densidades))
    semillas += [semillas[-1]] * (n - len(semillas))
    densidades += [densidades[-1]] * (n - len(densidades))

    fig = plt.figure()
    axes = []

    for i in range(n):
        if modo == "3D":
            ax = fig.add_subplot(1, n, i + 1, projection="3d")
        else:
            ax = fig.add_subplot(1, n, i + 1)
        axes.append(ax)

        seed = semillas[i]
        density = densidades[i]

        if callable(fractal):
            data = np.asarray(fractal(seed=seed, density=density))
        else:
            data = np.asarray(fractal)
        data = _preprocesar_datos(data, cortes, proyeccion)

        x = np.arange(data.shape[0])
        y = np.arange(data.shape[1])
        X, Y = np.meshgrid(x, y)

        if modo == "3D":
            ax.plot_surface(X, Y, data, cmap="viridis")
        else:
            ax.imshow(data, cmap="viridis")

        titulo = "Fractal"
        if seed is not None:
            titulo += f" seed={seed}"
        if density is not None:
            titulo += f" density={density}"
        ax.set_title(titulo)

    fig.suptitle("Visualización de fractales")
    return fig, axes


def visualizar_dinamica(fractal_dinamico, interval=200, cortes=None, proyeccion="mean"):
    """Genera una animación a partir de una secuencia de matrices.

    Parameters
    ----------
    fractal_dinamico:
        Secuencia (lista o generador) de matrices 2D.
    interval:
        Tiempo entre cuadros en milisegundos.
    cortes, proyeccion:
        Parámetros de :func:`visualizar_fractal` para manejar dimensiones
        superiores.
    """

    frames = [np.asarray(f) for f in fractal_dinamico]
    if not frames:
        raise ValueError("La secuencia de fractales está vacía.")
    frames = [_preprocesar_datos(f, cortes, proyeccion) for f in frames]

    fig, ax = plt.subplots()
    imagen = ax.imshow(frames[0], cmap="viridis")

    def actualizar(i):
        imagen.set_array(frames[i])
        return [imagen]

    animacion = FuncAnimation(fig, actualizar, frames=len(frames), interval=interval, blit=True)
    return fig, ax, animacion
