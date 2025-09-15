"""Demostración del algoritmo evolutivo de grupos."""

from holobit_sdk.quantum_holocron.core.holocron import Holocron
import random


def main():
    holocron = Holocron()
    for i in range(1, 6):
        holocron.add_holobit(f"H{i}", i)
    holocron.create_group("G", ["H1", "H2"])

    def fitness(grupo):
        return sum(grupo)

    random.seed(0)
    holocron.evolve_groups(fitness, generations=5, population_size=10)

    ids = [hid for hid, hb in holocron.holobits.items() if hb in holocron.groups["G"]]
    print("Grupo evolucionado:", ids)


if __name__ == "__main__":
    main()
