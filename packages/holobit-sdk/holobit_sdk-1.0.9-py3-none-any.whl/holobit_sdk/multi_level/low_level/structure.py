import numpy as np

class HoloStructure:
    """Agrupa varios Holobits permitiendo transformaciones colectivas."""

    def __init__(self, holobit_ids, memory_manager):
        self.holobit_ids = list(holobit_ids)
        self.memory = memory_manager

    def _apply_to_all(self, func):
        nuevas_pos = {}
        for hid in self.holobit_ids:
            pos = np.array(self.memory.get_position(hid), dtype=float)
            nuevas_pos[hid] = func(pos)
        for hid in self.holobit_ids:
            self.memory.deallocate(hid)
        for hid, pos in nuevas_pos.items():
            self.memory.allocate(hid, tuple(map(float, pos)))

    def translate(self, vector):
        vector = np.array(vector, dtype=float)
        self._apply_to_all(lambda p: p + vector)

    def scale(self, factor):
        self._apply_to_all(lambda p: p * float(factor))

    def rotate(self, axis, angle_degrees):
        angle = np.radians(float(angle_degrees))
        c, s = np.cos(angle), np.sin(angle)
        if axis == 'x':
            R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == 'y':
            R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        elif axis == 'z':
            R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        else:
            raise ValueError("Eje desconocido")
        self._apply_to_all(lambda p: R @ p)
