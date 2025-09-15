"""Demostración paso a paso del algoritmo de superposición y medición."""

import random
import sys
from pathlib import Path

# Permite ejecutar el ejemplo sin instalar el paquete
sys.path.append(str(Path(__file__).resolve().parents[1]))

from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.quantum_holocron import ejecutar_superposicion_medicion


def main():
    print("Inicializando Holocron...")
    holocron = Holocron()

    print("Añadiendo Holobits de ejemplo al Holocron...")
    for i in range(3):
        holocron.add_holobit(f"hb{i}", i)
        print(f"  Holobit hb{i} añadido")

    print("Creando un grupo con los Holobits añadidos...")
    holocron.create_group("grupo_demo", ["hb0", "hb1", "hb2"])
    print("Grupo 'grupo_demo' creado.")

    print("\nEjecutando el algoritmo de superposición y medición...")
    random.seed(42)
    resultados = ejecutar_superposicion_medicion(holocron, "grupo_demo")
    print(f"Resultados de la medición: {resultados}")


if __name__ == "__main__":
    main()
