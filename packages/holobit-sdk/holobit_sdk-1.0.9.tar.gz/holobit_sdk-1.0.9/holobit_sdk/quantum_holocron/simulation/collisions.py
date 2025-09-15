import numpy as np


def center_of_mass(holobit):
    """Calcula el centro de masa de un Holobit."""
    posiciones = np.array([q.posicion for q in holobit.quarks + holobit.antiquarks])
    return posiciones.mean(axis=0)


def calculate_trajectory(holobit, velocidad, pasos=10, dt=1.0):
    """Genera la trayectoria del centro de masa de un Holobit.

    Args:
        holobit: Objeto ``Holobit`` cuya trayectoria se calcula.
        velocidad: Vector de velocidad ``(vx, vy, vz)``.
        pasos: Número de pasos a simular.
        dt: Intervalo de tiempo entre pasos.

    Returns:
        ``numpy.ndarray`` con las posiciones del centro de masa en cada paso.
    """
    velocidad = np.asarray(velocidad, dtype=float)
    inicio = center_of_mass(holobit)
    return np.array([inicio + velocidad * i * dt for i in range(pasos)])


def detect_collision(trayectoria1, trayectoria2, umbral=0.1):
    """Detecta el primer impacto entre dos trayectorias.

    Args:
        trayectoria1: Posiciones del primer Holobit.
        trayectoria2: Posiciones del segundo Holobit.
        umbral: Distancia mínima para considerar una colisión.

    Returns:
        Índice del paso donde ocurre la colisión o ``None`` si no hay impacto.
    """
    distancias = np.linalg.norm(trayectoria1 - trayectoria2, axis=1)
    indices = np.where(distancias < umbral)[0]
    return int(indices[0]) if indices.size else None


def simulate_collision(h1, h2, parametros):
    """Simula la colisión entre dos Holobits y calcula magnitudes básicas.

    Args:
        h1: Primer Holobit.
        h2: Segundo Holobit.
        parametros: Diccionario con ``v1``, ``v2``, ``pasos``, ``dt`` y ``umbral``.

    Returns:
        Diccionario con las trayectorias y resultados de la colisión.
    """
    v1 = np.asarray(parametros.get("v1", [0, 0, 0]), dtype=float)
    v2 = np.asarray(parametros.get("v2", [0, 0, 0]), dtype=float)
    pasos = int(parametros.get("pasos", 10))
    dt = float(parametros.get("dt", 1.0))
    umbral = float(parametros.get("umbral", 0.1))

    tray1 = calculate_trajectory(h1, v1, pasos, dt)
    tray2 = calculate_trajectory(h2, v2, pasos, dt)
    paso_col = detect_collision(tray1, tray2, umbral)

    resultado = {"trayectoria1": tray1, "trayectoria2": tray2, "paso_colision": paso_col}
    if paso_col is not None:
        energia = 0.5 * np.linalg.norm(v1 - v2) ** 2
        dispersion = np.linalg.norm(tray1[paso_col] - tray2[paso_col])
        resultado.update({"energia": energia, "dispersion": dispersion})
    return resultado
