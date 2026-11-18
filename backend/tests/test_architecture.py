# Übung 5: Architekturregeln als Test, wie JDepend in den Kursmaterialien (MET, CCD).

"""Architekturregeln als Test (Kursmaterialien MET 5.8.2 und CCD 6.7).

Die Kursmaterialien zeigen, wie JDepend die Zyklenfreiheit als JUnit-Test in den Build
einbindet. Dieser Test macht dasselbe für Python: Er liest die Imports aller
Module und prüft die Regeln aus Übung 4.
"""

import ast
from collections import defaultdict
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
CONTEXTS = {"catalog", "circles", "discussion", "reading"}
FRAMEWORKS = ("fastapi", "sqlalchemy", "psycopg")


def imports_by_module() -> dict[str, set[str]]:
    """Ordnet jedem Modul (z. B. 'app.catalog.domain.book') seine Imports zu."""
    result = {}
    for path in APP.rglob("*.py"):
        module = ".".join(path.relative_to(APP.parent).with_suffix("").parts)
        names = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        result[module] = names
    return result


def package_of(module: str) -> str:
    """'app.catalog.domain.book' -> 'catalog', 'app.main' -> 'main'."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else parts[0]


def package_graph() -> dict[str, set[str]]:
    graph = defaultdict(set)
    for module, imported in imports_by_module().items():
        source = package_of(module)
        for name in imported:
            if name.startswith("app."):
                target = package_of(name)
                if target != source:
                    graph[source].add(target)
    return graph


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Tiefensuche. Gibt einen Zyklus wie ['a', 'b', 'a'] zurück oder None."""
    visiting, done = [], set()

    def visit(node):
        if node in visiting:
            return [*visiting[visiting.index(node) :], node]
        if node in done:
            return None
        visiting.append(node)
        for nxt in sorted(graph.get(node, ())):
            if cycle := visit(nxt):
                return cycle
        visiting.pop()
        done.add(node)
        return None

    for start in sorted(graph):
        if cycle := visit(start):
            return cycle
    return None


def test_find_cycle_detects_cycles():
    """Der Prüfer selbst muss funktionieren, sonst ist der Test wertlos."""
    assert find_cycle({"a": {"b"}, "b": {"c"}, "c": {"a"}}) == ["a", "b", "c", "a"]
    assert find_cycle({"a": {"b"}, "b": {"c"}}) is None


def test_no_cycles_between_packages():
    """Acyclic Dependencies Principle: Pakete dürfen sich nicht zyklisch importieren."""
    assert find_cycle(package_graph()) is None


def test_bounded_contexts_do_not_import_each_other():
    """Contexts kommunizieren nur über shared (Events, Fehler), nie direkt."""
    for source, targets in package_graph().items():
        if source in CONTEXTS:
            assert not targets & CONTEXTS, f"{source} importiert {targets & CONTEXTS}"


def test_shared_does_not_depend_on_contexts():
    """shared ist das stabilste Paket (Stable Dependencies Principle)."""
    assert not package_graph().get("shared", set()) & CONTEXTS


def test_domain_layer_is_framework_free():
    """Die Domain-Schicht ist reines Python: kein FastAPI, keine Datenbank,
    keine Imports aus application, infrastructure oder api."""
    for module, imported in imports_by_module().items():
        if ".domain." not in module:
            continue
        for name in imported:
            assert not name.startswith(FRAMEWORKS), f"{module} importiert {name}"
            assert not any(
                f".{layer}" in name
                for layer in ("application", "infrastructure", "api")
            ), f"{module} importiert {name}"
