"""Backend para generar código Go a partir del AST de HoloLang."""

from typing import List, Dict, Any


class GoBackend:
    """Traduce el AST de HoloLang a código Go."""

    def translate(self, ast: List[Dict[str, Any]]) -> str:
        lines: List[str] = ["package main", "", "import \"fmt\"", "", "func main() {"]
        lines.extend(self._translate_ast(ast, 1))
        lines.append("}")
        return "\n".join(lines)

    def _translate_ast(self, ast: List[Dict[str, Any]], indent: int) -> List[str]:
        lines: List[str] = []
        for node in ast:
            lines.extend(self._translate_node(node, indent))
        return lines

    def _translate_node(self, node: Dict[str, Any], indent: int) -> List[str]:
        tab = "    " * indent
        tipo = node.get("type")
        if tipo == "INSTR":
            return [f"{tab}// {node['code']}"]
        if tipo in {"IF", "QIF"}:
            lines = [f"{tab}if {node['condition']} {{"]
            lines.extend(self._translate_ast(node["body"], indent + 1))
            if "else" in node:
                lines.append(f"{tab}}} else {{")
                lines.extend(self._translate_ast(node["else"], indent + 1))
            lines.append(f"{tab}}}")
            return lines
        if tipo == "FOR":
            if "count" in node:
                lines = [f"{tab}for _i := 0; _i < {node['count']}; _i++ {{"]
            else:
                var = node.get("var", "i")
                start = node.get("start", 0)
                end = node.get("end", 0)
                lines = [f"{tab}for {var} := {start}; {var} <= {end}; {var}++ {{"]
            lines.extend(self._translate_ast(node["body"], indent + 1))
            lines.append(f"{tab}}}")
            return lines
        if tipo == "WHILE":
            lines = [f"{tab}for _w := 0; _w < {node['condition']}; _w++ {{"]
            lines.extend(self._translate_ast(node["body"], indent + 1))
            lines.append(f"{tab}}}")
            return lines
        if tipo == "SWITCH":
            lines = [f"{tab}switch {node['expr']} {{"]
            for case in node.get("cases", []):
                match = case["match"]
                if match == "DEFAULT":
                    lines.append(f"{tab}default:")
                else:
                    lines.append(f"{tab}case {match}:")
                lines.extend(self._translate_ast(case["body"], indent + 1))
                lines.append(f"{tab}    break")
            lines.append(f"{tab}}}")
            return lines
        return []
