import matplotlib.pyplot as plt


def proyectar_holograma(holobits):
    """
    Proyecta las posiciones de los quarks y antiquarks de una lista de
    holobits en una figura 3D. Cada holobit muestra su valor de spin en el
    centro geométrico calculado a partir de todas sus partículas.

    Args:
        holobits: Lista de objetos ``Holobit``.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    for holobit in holobits:
        for quark in holobit.quarks:
            ax.scatter(
                quark.posicion[0],
                quark.posicion[1],
                quark.posicion[2],
                color="blue",
            )
        for antiquark in holobit.antiquarks:
            ax.scatter(
                antiquark.posicion[0],
                antiquark.posicion[1],
                antiquark.posicion[2],
                color="red",
            )

        todas = holobit.quarks + holobit.antiquarks
        centro = sum((p.posicion for p in todas)) / len(todas)
        ax.text(centro[0], centro[1], centro[2], f"spin={holobit.spin}")

    ax.set_title("Proyección Holográfica de Holobits")
    return fig, ax


def visualizar_familia_3d(holobits):
    """
    Genera una visualización 3D para una familia de holobits.

    Args:
        holobits: Lista de objetos ``Holobit``.
    """
    fig, ax = proyectar_holograma(holobits)
    plt.show()
    return fig, ax

