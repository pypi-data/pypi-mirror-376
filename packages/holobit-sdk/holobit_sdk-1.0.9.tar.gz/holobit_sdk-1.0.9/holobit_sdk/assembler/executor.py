class AssemblerExecutor:
    def __init__(self, parser):
        """
        Ejecuta instrucciones ensambladas.

        Args:
            parser: Objeto AssemblerParser.
        """
        self.parser = parser

    def execute(self, command):
        """
        Ejecuta una instrucción ensamblada.

        Args:
            command: Línea ensamblada para ejecutar.
        """
        self.parser.parse_line(command)
