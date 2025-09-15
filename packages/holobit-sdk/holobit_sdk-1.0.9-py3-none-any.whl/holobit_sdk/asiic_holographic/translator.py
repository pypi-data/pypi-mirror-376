"""Traductor del ASIIC Holográfico a ensamblador.

Correspondencia de instrucciones ASIIC → ensamblador:

- ``CREAR`` → ``CREAR``
- ``CREAR_HOLOBIT`` → ``CREAR_HOLOBIT``
- ``ROTAR`` → ``ROT``
- ``ROT`` → ``ROT``
- ``ENTRELAZAR`` → ``ENTR``
- ``ENTR`` → ``ENTR``
- ``SUPERPOS`` → ``SUPERPOS``
- ``MEDIR`` → ``MEDIR``
- ``ENTANGLE`` → ``ENTANGLE``
- ``CREAR_GRUPO``/``GRUPO`` → ``GRUPO``
"""


class ASIICTranslator:
    """Convierte comandos del ASIIC Holográfico al ensamblador."""

    def __init__(self):
        self.mapeo_instrucciones = {
            "CREAR": "CREAR",
            "CREAR_HOLOBIT": "CREAR_HOLOBIT",
            "ROTAR": "ROT",
            "ROT": "ROT",
            "ENTRELAZAR": "ENTR",
            "ENTR": "ENTR",
            "SUPERPOS": "SUPERPOS",
            "MEDIR": "MEDIR",
            "ENTANGLE": "ENTANGLE",
            "CREAR_GRUPO": "GRUPO",
            "GRUPO": "GRUPO",
        }

    def traducir(self, comando):
        """
        Convierte un comando ASIIC en su equivalente en lenguaje ensamblador holográfico.

        Args:
            comando (str): Comando ASIIC a traducir.

        Returns:
            str: Comando traducido al ensamblador holográfico.
        """
        partes = comando.split()
        if not partes:
            return "Comando vacío"

        nombre = partes[0].upper()
        argumentos = " ".join(partes[1:])

        if nombre in self.mapeo_instrucciones:
            return f"{self.mapeo_instrucciones[nombre]} {argumentos}"
        else:
            return f"Instrucción desconocida: {nombre}"


# Ejemplo de uso
if __name__ == "__main__":
    traductor = ASIICTranslator()

    # Pruebas de traducción
    print(traductor.traducir("ROTAR H1 z 90"))  # Debe devolver "ROT H1 z 90"
    print(traductor.traducir("ENTRELAZAR H1 H2"))  # Debe devolver "ENTR H1 H2"
    print(traductor.traducir("DESCONOCIDO X Y Z"))  # Debe devolver "Instrucción desconocida: DESCONOCIDO"

