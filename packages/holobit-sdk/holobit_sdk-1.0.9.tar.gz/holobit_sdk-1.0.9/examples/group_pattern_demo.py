from holobit_sdk.assembler.parser import AssemblerParser


def main():
    parser = AssemblerParser()
    for i in range(1, 7):
        parser.parse_line(f"CREAR Q{i} ({i*0.1}, {i*0.2}, {i*0.3})")
    parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
    parser.parse_line("CREAR H2 {Q1, Q2, Q3, Q4, Q5, Q6}")
    parser.parse_line("CREAR HX {Q1, Q2, Q3, Q4, Q5, Q6}")
    parser.parse_line("AGRUPAR G /H[0-9]/")
    group = parser.holocron.groups["G"]
    nombres = [name for name, hb in parser.holocron.holobits.items() if hb in group]
    print("Holobits en el grupo G:", nombres)


if __name__ == "__main__":
    main()
