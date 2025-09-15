from holobit_sdk.asiic_holographic.translator import ASIICTranslator
from holobit_sdk.assembler.virtual_machine import AssemblerVM


class ASIICInterpreter:
    """Intérprete del ASIIC Holográfico."""

    def __init__(self, vm: AssemblerVM | None = None):
        """Inicializa el intérprete con una VM opcional."""
        self.vm = vm if vm is not None else AssemblerVM()
        self.translator = ASIICTranslator()

    def interpretar(self, comando):
        """Traduce y ejecuta un comando ASIIC."""

        asm_command = self.translator.traducir(comando)
        if (
            asm_command.startswith("Instrucción desconocida")
            or asm_command == "Comando vacío"
        ):
            return asm_command

        parts = asm_command.split()
        instr = parts[0]
        args = parts[1:]

        try:
            self.vm.execute_instruction(instr, *args)
        except ValueError as e:
            return str(e)

        return asm_command


# Ejemplo de uso
if __name__ == "__main__":
    interprete = ASIICInterpreter()

    # Ejecutar comandos de prueba
    print(interprete.interpretar("ROTAR H1 z 90"))
    print(interprete.interpretar("ENTRELAZAR H1 H2"))
