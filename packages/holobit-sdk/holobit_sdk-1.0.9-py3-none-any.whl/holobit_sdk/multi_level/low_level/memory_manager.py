import numpy as np

class FractalMemoryNode:
    """Nodo de memoria que puede subdividirse recursivamente."""

    def __init__(self, inicio, tamano, profundidad=0, profundidad_max=4):
        self.inicio = np.array(inicio, dtype=float)
        self.tamano = float(tamano)
        self.profundidad = profundidad
        self.profundidad_max = profundidad_max
        self.holobit_id = None
        self.posicion = None
        self.hijos = None

    def _indice_hijo(self, posicion):
        mitad = self.inicio + self.tamano / 2
        indice = 0
        if posicion[0] >= mitad[0]:
            indice |= 1
        if posicion[1] >= mitad[1]:
            indice |= 2
        if posicion[2] >= mitad[2]:
            indice |= 4
        return indice

    def _crear_hijos(self):
        mitad = self.tamano / 2
        self.hijos = []
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    inicio = (
                        self.inicio[0] + dx * mitad,
                        self.inicio[1] + dy * mitad,
                        self.inicio[2] + dz * mitad,
                    )
                    nodo = FractalMemoryNode(
                        inicio, mitad, self.profundidad + 1, self.profundidad_max
                    )
                    self.hijos.append(nodo)

    def _hijo_para(self, posicion):
        if self.hijos is None:
            raise ValueError("El nodo no está subdividido")
        return self.hijos[self._indice_hijo(posicion)]

    def esta_vacio(self):
        if self.hijos is not None:
            return all(hijo.esta_vacio() for hijo in self.hijos)
        return self.holobit_id is None

    def allocate(self, holobit_id, posicion):
        if self.hijos is not None:
            self._hijo_para(posicion).allocate(holobit_id, posicion)
        else:
            if self.holobit_id is None:
                self.holobit_id = holobit_id
                self.posicion = tuple(map(float, posicion))
            else:
                if self.profundidad >= self.profundidad_max:
                    raise MemoryError("Memoria holográfica llena.")
                existente = (self.holobit_id, self.posicion)
                self.holobit_id = None
                self.posicion = None
                self._crear_hijos()
                self._hijo_para(existente[1]).allocate(*existente)
                self._hijo_para(posicion).allocate(holobit_id, posicion)

    def deallocate(self, holobit_id):
        if self.hijos is not None:
            for hijo in self.hijos:
                if hijo.deallocate(holobit_id):
                    if all(h.esta_vacio() for h in self.hijos):
                        self.hijos = None
                    return True
            return False
        else:
            if self.holobit_id == holobit_id:
                self.holobit_id = None
                self.posicion = None
                return True
            return False

    def get_position(self, holobit_id):
        if self.hijos is not None:
            for hijo in self.hijos:
                pos = hijo.get_position(holobit_id)
                if pos is not None:
                    return pos
            return None
        else:
            if self.holobit_id == holobit_id:
                return self.posicion
            return None


class MemoryManager:
    """Administrador de memoria basado en un árbol fractal."""

    def __init__(self, size=1.0, profundidad_max=4):
        self.raiz = FractalMemoryNode((0.0, 0.0, 0.0), size, 0, profundidad_max)

    def allocate(self, holobit_id, posicion):
        if self.exists(holobit_id):
            raise ValueError(f"El Holobit {holobit_id} ya está asignado.")
        self.raiz.allocate(holobit_id, posicion)

    def deallocate(self, holobit_id):
        if not self.raiz.deallocate(holobit_id):
            raise KeyError(f"El Holobit {holobit_id} no está en la memoria.")

    def get_position(self, holobit_id):
        pos = self.raiz.get_position(holobit_id)
        if pos is None:
            raise KeyError(f"El Holobit {holobit_id} no está en la memoria.")
        return pos

    def exists(self, holobit_id):
        return self.raiz.get_position(holobit_id) is not None


if __name__ == "__main__":
    mem_manager = MemoryManager()
    mem_manager.allocate("H1", (0.1, 0.2, 0.3))
    print("Posición de H1:", mem_manager.get_position("H1"))
    mem_manager.deallocate("H1")
