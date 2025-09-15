import re
import copy
from .group_evolution import evolve_group_ids


class Holocron:
    """
    Representa un Holocron Cuántico que almacena y gestiona grupos de Holobits.
    """

    def __init__(self):
        self.holobits = {}  # Almacena los Holobits por identificador
        self.groups = {}   # Almacena grupos de Holobits
        self._states = {}  # Estados clonados del Holocron

    def add_holobit(self, id, holobit):
        """
        Añade un Holobit al Holocron.
        """
        self.holobits[id] = holobit

    def create_group(self, group_id, holobit_ids):
        """
        Crea un grupo de Holobits.
        """
        group = [self.holobits[hid] for hid in holobit_ids if hid in self.holobits]
        if len(group) != len(holobit_ids):
            raise ValueError("Algunos Holobits no existen en el Holocron.")
        self.groups[group_id] = group

    def create_group_from_pattern(self, group_id, pattern):
        """Crea un grupo a partir de un patrón de expresiones regulares.

        Parameters
        ----------
        group_id: str
            Identificador del grupo a crear.
        pattern: str
            Expresión regular utilizada para seleccionar los Holobits.

        Raises
        ------
        ValueError
            Si ningún Holobit coincide con el patrón proporcionado.
        """

        regex = re.compile(pattern)
        seleccionados = [hid for hid in self.holobits if regex.fullmatch(hid)]
        if not seleccionados:
            raise ValueError(
                "Ningún Holobit coincide con el patrón especificado.")
        self.groups[group_id] = [self.holobits[hid] for hid in seleccionados]

    def merge_groups(self, new_group_id, group_ids):
        """Fusiona múltiples grupos en uno nuevo.

        Parameters
        ----------
        new_group_id: str
            Identificador del nuevo grupo resultante.
        group_ids: Iterable[str]
            Colección con los identificadores de los grupos a fusionar.

        Notes
        -----
        Los grupos originales se eliminan del Holocron tras la fusión.
        """
        merged = []
        for gid in group_ids:
            if gid not in self.groups:
                raise KeyError(f"El grupo '{gid}' no existe.")
            merged.extend(self.groups[gid])
        self.groups[new_group_id] = merged
        for gid in group_ids:
            self.groups.pop(gid, None)

    def save_state(self, name):
        """Guarda una copia del estado actual del Holocron.

        Parameters
        ----------
        name: str
            Identificador bajo el que se almacenará el estado.

        Notes
        -----
        Se guardan copias independientes de ``holobits`` y ``groups`` para
        evitar efectos secundarios al modificar el Holocron tras el guardado.
        """

        self._states[name] = {
            "holobits": copy.deepcopy(self.holobits),
            "groups": copy.deepcopy(self.groups),
        }

    def restore_state(self, name):
        """Restaura un estado previamente guardado."""

        if name not in self._states:
            raise KeyError(f"El estado '{name}' no existe en el Holocron.")

        data = self._states[name]
        self.holobits = copy.deepcopy(data["holobits"])
        self.groups = copy.deepcopy(data["groups"])

    def compare_states(self, a, b):
        """Compara dos estados guardados del Holocron.

        Parameters
        ----------
        a, b : str
            Identificadores de los estados a comparar.

        Returns
        -------
        bool | dict
            ``True`` si ambos estados son idénticos. En caso contrario se
            devuelve un diccionario con las diferencias encontradas.
        """

        if a not in self._states or b not in self._states:
            raise KeyError("Uno de los estados no existe en el Holocron.")

        state_a = self._states[a]
        state_b = self._states[b]

        if state_a == state_b:
            return True

        diff = {}
        for key in set(state_a) | set(state_b):
            if state_a.get(key) != state_b.get(key):
                diff[key] = {"a": state_a.get(key), "b": state_b.get(key)}
        return diff

    def split_group(self, source_group_id, new_group_id, holobit_ids):
        """Divide un grupo moviendo ciertos Holobits a otro grupo.

        Parameters
        ----------
        source_group_id: str
            Grupo que se desea dividir.
        new_group_id: str
            Identificador del nuevo grupo creado con los Holobits extraídos.
        holobit_ids: Iterable[str]
            Identificadores de los Holobits que pasarán al nuevo grupo.
        """
        if source_group_id not in self.groups:
            raise KeyError(f"El grupo '{source_group_id}' no existe.")

        source_group = self.groups[source_group_id]
        moving = []
        for hid in holobit_ids:
            if hid not in self.holobits:
                raise KeyError(f"El Holobit '{hid}' no existe en el Holocron.")
            holobit = self.holobits[hid]
            if holobit not in source_group:
                raise ValueError(
                    f"El Holobit '{hid}' no pertenece al grupo '{source_group_id}'."
                )
            moving.append(holobit)

        # Actualizar grupos
        self.groups[source_group_id] = [hb for hb in source_group if hb not in moving]
        self.groups[new_group_id] = moving

    def evolve_groups(self, criteria_fn, generations, population_size):
        """Aplica un algoritmo evolutivo sobre todos los grupos.

        Parameters
        ----------
        criteria_fn: Callable[[list], float]
            Función que evalúa la aptitud de un grupo. Debe devolver un valor
            numérico que se **maximiza**. Para minimizar un criterio, se puede
            retornar su valor negativo.
        generations: int
            Número de generaciones a simular.
        population_size: int
            Tamaño de la población de candidatos por generación.
        """

        reverse = {hb: hid for hid, hb in self.holobits.items()}
        for gid, group in list(self.groups.items()):
            initial_ids = [reverse[hb] for hb in group]
            evolved_ids = evolve_group_ids(
                initial_ids, self.holobits, criteria_fn, generations, population_size
            )
            self.groups[gid] = [self.holobits[hid] for hid in evolved_ids]

    def execute_quantum_operation(self, operation, group_ids):
        """
        Ejecuta una operación cuántica sobre uno o varios grupos de Holobits.

        Si ``group_ids`` es una colección, todos los Holobits de los grupos
        indicados se combinarán antes de aplicar la operación. Esto permite
        realizar operaciones de entrelazamiento entre grupos completos.
        """

        if isinstance(group_ids, (list, tuple, set)):
            combined_group = []
            for gid in group_ids:
                if gid not in self.groups:
                    raise KeyError(f"El grupo '{gid}' no existe.")
                combined_group.extend(self.groups[gid])
            return operation.apply(combined_group)

        if group_ids not in self.groups:
            raise KeyError(f"El grupo '{group_ids}' no existe.")
        group = self.groups[group_ids]
        return operation.apply(group)

    def execute_parallel_operations(self, mapping):
        """Ejecuta múltiples operaciones cuánticas en paralelo.

        Parameters
        ----------
        mapping: dict
            Diccionario donde la clave es una operación cuántica y el valor el
            identificador del grupo sobre el que se aplicará.

        Returns
        -------
        dict
            Resultados de cada operación indexados por el identificador del
            grupo correspondiente.
        """

        from concurrent.futures import ThreadPoolExecutor

        resultados = {}

        def _aplicar(op, gid):
            if gid not in self.groups:
                raise KeyError(f"El grupo '{gid}' no existe.")
            grupo = self.groups[gid]
            resultado = op.apply(grupo)
            self.groups[gid] = resultado
            resultados[gid] = resultado

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(_aplicar, op, gid) for op, gid in mapping.items()]
            for future in futures:
                future.result()

        return resultados

    def apply_interaction(self, interaction, group_id, *args, **kwargs):
        """Aplica una interacción física sobre un grupo de Holobits.

        La interacción puede aceptar una lista completa de Holobits o
        procesarlos individualmente. Los argumentos adicionales se
        propagan a la función de interacción.
        """
        if group_id not in self.groups:
            raise KeyError(f"El grupo '{group_id}' no existe.")
        group = self.groups[group_id]
        try:
            return interaction(group, *args, **kwargs)
        except (TypeError, AttributeError):
            return [interaction(hb, *args, **kwargs) for hb in group]

    def synchronize_measurements(self, group_ids):
        """Sincroniza las mediciones entre varios grupos de Holobits.

        El primer grupo de ``group_ids`` se mide utilizando la función
        :func:`medir` y su resultado se replica en los demás grupos mediante
        ``apply_interaction``. Todos los grupos terminan compartiendo la misma
        medición, que se devuelve en un diccionario asociando el identificador
        del grupo con la lista de mediciones.
        """

        if len(group_ids) < 2:
            raise ValueError("Se requieren al menos dos grupos para sincronizar.")

        for gid in group_ids:
            if gid not in self.groups:
                raise KeyError(f"El grupo '{gid}' no existe.")

        from ..quantum_algorithm import medir

        referencia_id = group_ids[0]
        resultados_referencia = self.apply_interaction(medir, referencia_id)

        def _replicar(_grupo, ref=resultados_referencia):
            # Ejecutamos la medición para mantener la semántica, pero
            # devolvemos siempre la referencia para sincronizar resultados.
            medir(_grupo)
            return ref

        resultados = {referencia_id: resultados_referencia}
        for gid in group_ids[1:]:
            resultados[gid] = self.apply_interaction(_replicar, gid)

        return resultados
