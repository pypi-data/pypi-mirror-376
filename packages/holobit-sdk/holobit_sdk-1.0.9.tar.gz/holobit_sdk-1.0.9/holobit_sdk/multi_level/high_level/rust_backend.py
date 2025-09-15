"""Backend para generar código Rust a partir del AST de HoloLang."""

from typing import List, Dict, Any


class RustBackend:
    """Traduce el AST de HoloLang a código Rust."""

    def translate(self, ast: List[Dict[str, Any]]) -> str:
        lines: List[str] = ["fn main() {"]
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
                lines = [f"{tab}for _i in 0..{node['count']} {{"]
            else:
                var = node.get("var", "i")
                start = node.get("start", 0)
                end = node.get("end", 0)
                lines = [f"{tab}for {var} in {start}..={end} {{"]
            lines.extend(self._translate_ast(node["body"], indent + 1))
            lines.append(f"{tab}}}")
            return lines
        if tipo == "WHILE":
            lines = [f"{tab}for _w in 0..{node['condition']} {{"]
            lines.extend(self._translate_ast(node["body"], indent + 1))
            lines.append(f"{tab}}}")
            return lines
        if tipo == "SWITCH":
            lines = [f"{tab}match {node['expr']} {{"]
            for case in node.get("cases", []):
                match = case["match"]
                if match == "DEFAULT":
                    lines.append(f"{tab}    _ => {{")
                else:
                    lines.append(f"{tab}    {match} => {{")
                lines.extend(self._translate_ast(case["body"], indent + 1))
                lines.append(f"{tab}    }},")
            lines.append(f"{tab}}}")
            return lines
        return []
