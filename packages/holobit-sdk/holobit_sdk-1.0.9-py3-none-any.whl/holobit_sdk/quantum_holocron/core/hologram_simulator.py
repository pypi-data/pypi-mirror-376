import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from ..simulation.collisions import simulate_collision as _simulate_collision


class HologramSimulator:
    """
    Simulador para visualizar operaciones cuánticas y holográficas en el Holocron.
    Incluye herramientas para mover y rotar Holobits paso a paso.
    """

    def simulate(self, holobits, operation):
        """
        Genera una simulación holográfica para una operación cuántica.
        """
        print(f"Simulando operación '{operation.name}' en {len(holobits)} Holobits...")
        result = operation.apply(holobits)
        print(f"Resultado: {result}")
        return result

    def simulate_steps(self, holobit, steps):
        """
        Aplica una serie de traslaciones y rotaciones a un Holobit.

        Args:
            holobit: Objeto ``Holobit`` a manipular.
            steps: Lista de diccionarios con las claves ``traslacion`` y
                ``rotacion``. ``traslacion`` debe ser una tupla ``(dx, dy, dz)`` y
                ``rotacion`` una tupla ``(eje, angulo)``.

        Returns:
            Lista con las posiciones de los quarks y antiquarks después de cada
            paso.
        """
        snapshots = []
        for step in steps:
            if "traslacion" in step:
                dx, dy, dz = step["traslacion"]
                delta = np.array([dx, dy, dz])
                for q in holobit.quarks + holobit.antiquarks:
                    q.posicion += delta
            if "rotacion" in step:
                eje, angulo = step["rotacion"]
                holobit.rotar(eje, angulo)
            snapshots.append([q.posicion.copy() for q in holobit.quarks + holobit.antiquarks])
        return snapshots

    def animate(self, holobit, steps, interval=500, output_path=None):
        """
        Visualiza en 3D la trayectoria y rotaciones de un Holobit.

        Args:
            holobit: Objeto ``Holobit`` a animar.
            steps: Pasos de movimiento utilizados por :meth:`simulate_steps`.
            interval: Tiempo entre fotogramas en milisegundos.
            output_path: Ruta opcional para guardar la animación en un archivo.
        """
        snapshots = self.simulate_steps(holobit, steps)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        quark_scatter = ax.scatter([], [], [], color='blue', label='Quark')
        antiquark_scatter = ax.scatter([], [], [], color='red', label='Antiquark')

        positions = np.array(snapshots).reshape(-1, 3)
        limit = float(np.abs(positions).max() or 1)
        ax.set_xlim(-limit, limit)
        ax.set_ylim(-limit, limit)
        ax.set_zlim(-limit, limit)

        def update(frame):
            pos = snapshots[frame]
            q_pos = pos[:len(holobit.quarks)]
            a_pos = pos[len(holobit.quarks):]
            quark_scatter._offsets3d = ([p[0] for p in q_pos],
                                        [p[1] for p in q_pos],
                                        [p[2] for p in q_pos])
            antiquark_scatter._offsets3d = ([p[0] for p in a_pos],
                                            [p[1] for p in a_pos],
                                            [p[2] for p in a_pos])
            ax.set_title(f"Paso {frame + 1}/{len(snapshots)}")
            return quark_scatter, antiquark_scatter

        ani = animation.FuncAnimation(
            fig,
            update,
            frames=len(snapshots),
            interval=interval,
            blit=False
        )
        plt.legend()
        if output_path:
            ani.save(output_path)
        plt.show()
        return ani

    def simulate_collision(self, h1, h2, parametros, interval=500, output_path=None):
        """Visualiza paso a paso la colisión entre dos Holobits.

        Args:
            h1: Primer Holobit.
            h2: Segundo Holobit.
            parametros: Diccionario de parámetros para
                :func:`~holobit_sdk.quantum_holocron.simulation.collisions.simulate_collision`.
            interval: Tiempo entre fotogramas en milisegundos.
            output_path: Ruta opcional para guardar la animación.

        Returns:
            Resultado devuelto por :func:`simulate_collision`.
        """
        resultado = _simulate_collision(h1, h2, parametros)
        tray1 = resultado["trayectoria1"]
        tray2 = resultado["trayectoria2"]

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        h1_scatter = ax.scatter([], [], [], color="blue", label="Holobit 1")
        h2_scatter = ax.scatter([], [], [], color="red", label="Holobit 2")

        limite = float(np.abs(np.concatenate([tray1, tray2])).max() or 1)
        ax.set_xlim(-limite, limite)
        ax.set_ylim(-limite, limite)
        ax.set_zlim(-limite, limite)

        def update(frame):
            p1 = tray1[frame]
            p2 = tray2[frame]
            h1_scatter._offsets3d = ([p1[0]], [p1[1]], [p1[2]])
            h2_scatter._offsets3d = ([p2[0]], [p2[1]], [p2[2]])
            ax.set_title(f"Paso {frame + 1}/{len(tray1)}")
            return h1_scatter, h2_scatter

        ani = animation.FuncAnimation(
            fig,
            update,
            frames=len(tray1),
            interval=interval,
            blit=False,
        )
        plt.legend()
        if output_path:
            ani.save(output_path)
        plt.show()
        return resultado
