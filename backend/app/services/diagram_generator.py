"""Generate a dependency-graph diagram from the files discovered in a repo.

The output is a dict with 'nodes' and 'edges' lists, ready for the
React Flow frontend.  Edges represent import relationships between
Python modules (and optionally JS/TS files).
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _module_id_from_path(rel_path: str) -> str:
    """Convert a relative file path to a dot-separated module id.

    Example: 'backend/app/services/cloner.py' -> 'backend.app.services.cloner'
    """
    return rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")


def _build_module_lookup(files: List[Dict[str, Any]], repo_path: Path) -> Dict[str, str]:
    """Build a lookup from every *possible* import form to the canonical node id.

    For 'backend/app/services/cloner.py' with id 'backend.app.services.cloner',
    we register:
      - 'backend.app.services.cloner'
      - 'app.services.cloner'
      - 'services.cloner'
      - 'cloner'
    so that import resolution can find the right node regardless of how the
    import is written.
    """
    lookup: Dict[str, str] = {}
    for f in files:
        if f.get("language") != "Python":
            continue
        rel = str(f["path"].relative_to(repo_path))
        node_id = _module_id_from_path(rel)
        parts = node_id.split(".")
        # Register every suffix of the module path
        for i in range(len(parts)):
            key = ".".join(parts[i:])
            # First match wins — more specific paths registered first
            if key not in lookup:
                lookup[key] = node_id
    return lookup


def _resolve_relative_import(source_module: str, module_name: str, level: int) -> str:
    """Resolve a relative import to an absolute module path.

    E.g. source='backend.app.services.evidence', level=1, module='cloner'
         -> 'backend.app.services.cloner'

    source='backend.app.services.evidence', level=2, module='models'
         -> 'backend.app.models'
    """
    parts = source_module.split(".")
    # Go up `level` directories (drop last `level` parts)
    if level >= len(parts):
        base_parts: list = []
    else:
        base_parts = parts[:-level]

    if module_name:
        return ".".join(base_parts + [module_name]) if base_parts else module_name
    return ".".join(base_parts) if base_parts else ""


# ---------------------------------------------------------------------------
# Python import extraction
# ---------------------------------------------------------------------------

def _extract_python_imports(
    file_path: Path,
    source_module: str,
    module_lookup: Dict[str, str],
    node_ids: Set[str],
) -> Tuple[List[Dict], List[Dict]]:
    """Parse a Python file and return (new_external_nodes, edges)."""
    new_nodes: List[Dict] = []
    edges: List[Dict] = []
    seen_edges: Set[Tuple[str, str]] = set()
    seen_external: Set[str] = set()

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return new_nodes, edges

    def _add_edge(src: str, tgt: str, label: str) -> None:
        if src == tgt:
            return
        key = (src, tgt)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": src, "target": tgt, "label": label})

    def _resolve_and_link(target_module: str, label: str) -> None:
        """Try to resolve *target_module* to a known project node."""
        # Direct match
        if target_module in module_lookup:
            _add_edge(source_module, module_lookup[target_module], label)
            return

        # Try progressively shorter suffixes
        parts = target_module.split(".")
        for i in range(len(parts)):
            suffix = ".".join(parts[i:])
            if suffix in module_lookup:
                _add_edge(source_module, module_lookup[suffix], label)
                return

        # External dependency — add a node for the top-level package
        ext_name = parts[0]
        if ext_name not in seen_external:
            seen_external.add(ext_name)
            if ext_name not in node_ids:
                new_nodes.append({
                    "id": ext_name,
                    "label": ext_name,
                    "type": "external",
                    "group": "external",
                })
                node_ids.add(ext_name)
        _add_edge(source_module, ext_name, "uses")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _resolve_and_link(alias.name, "imports")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.level and node.level > 0:
                    abs_module = _resolve_relative_import(
                        source_module, node.module, node.level
                    )
                else:
                    abs_module = node.module
                _resolve_and_link(abs_module, "imports")
            elif node.level and node.level > 0:
                # `from . import something`
                abs_module = _resolve_relative_import(
                    source_module, "", node.level
                )
                for alias in node.names:
                    full = f"{abs_module}.{alias.name}" if abs_module else alias.name
                    _resolve_and_link(full, "imports")

    return new_nodes, edges


# ---------------------------------------------------------------------------
# JS / TS import extraction (basic regex-based)
# ---------------------------------------------------------------------------

_JS_IMPORT_RE = re.compile(
    r"""(?:import|require)\s*\(?['"]\s*([^'"]+)['"]\s*\)?""",
    re.MULTILINE,
)


def _extract_js_imports(
    file_path: Path,
    source_node_id: str,
    node_ids: Set[str],
    file_node_map: Dict[str, str],
) -> Tuple[List[Dict], List[Dict]]:
    """Extract edges from JS/TS import/require statements."""
    new_nodes: List[Dict] = []
    edges: List[Dict] = []
    seen_edges: Set[Tuple[str, str]] = set()

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return new_nodes, edges

    def _add_edge(src: str, tgt: str, label: str) -> None:
        if src == tgt:
            return
        key = (src, tgt)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": src, "target": tgt, "label": label})

    for match in _JS_IMPORT_RE.finditer(source):
        import_path = match.group(1)

        if import_path.startswith("."):
            # Resolve relative import against the file's directory
            base_dir = file_path.parent
            resolved = (base_dir / import_path).resolve()
            # Try common extensions
            candidates = [resolved, resolved.with_suffix(".js"), resolved.with_suffix(".jsx"),
                          resolved.with_suffix(".ts"), resolved.with_suffix(".tsx")]
            for cand in candidates:
                cand_str = str(cand)
                if cand_str in file_node_map:
                    _add_edge(source_node_id, file_node_map[cand_str], "imports")
                    break
        else:
            # External package
            ext_name = import_path.split("/")[0]
            if ext_name.startswith("@") and "/" in import_path:
                ext_name = "/".join(import_path.split("/")[:2])
            if ext_name not in node_ids:
                new_nodes.append({
                    "id": ext_name,
                    "label": ext_name,
                    "type": "external",
                    "group": "external",
                })
                node_ids.add(ext_name)
            _add_edge(source_node_id, ext_name, "uses")

    return new_nodes, edges


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SUPPORTED_LANGUAGES = {"Python", "JavaScript", "TypeScript"}


def generate_diagram(repo_path: Path, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a dependency diagram from discovered source files.

    Returns ``{"nodes": [...], "edges": [...]}`` ready for React Flow.
    """
    nodes: List[Dict] = []
    node_ids: Set[str] = set()
    file_node_map: Dict[str, str] = {}  # abs path str -> node id (for JS resolution)

    try:
        # ---- Step 1: Create nodes for all source files ----
        for f in files:
            lang = f.get("language")
            if lang not in _SUPPORTED_LANGUAGES:
                continue

            rel_path = str(f["path"].relative_to(repo_path))

            if lang == "Python":
                node_id = _module_id_from_path(rel_path)
            else:
                node_id = rel_path.replace("/", ".").replace("\\", ".")

            if node_id in node_ids:
                continue

            label = rel_path.split("/")[-1]
            group = str(f["path"].parent.relative_to(repo_path)) if f["path"].parent != repo_path else "root"

            # __init__.py represents a package — use the package name as label
            file_type = "file"
            if label == "__init__.py":
                package_name = group.split("/")[-1] if group != "root" else "root"
                label = f"📦 {package_name}"
                file_type = "package"

            nodes.append({
                "id": node_id,
                "label": label,
                "type": file_type,
                "group": group,
            })
            node_ids.add(node_id)
            file_node_map[str(f["path"].resolve())] = node_id

        # ---- Step 2: Build import lookup for Python ----
        module_lookup = _build_module_lookup(files, repo_path)

        # ---- Step 3: Extract edges ----
        all_edges: List[Dict] = []

        for f in files:
            lang = f.get("language")
            if lang not in _SUPPORTED_LANGUAGES:
                continue

            rel_path = str(f["path"].relative_to(repo_path))

            if lang == "Python":
                source_module = _module_id_from_path(rel_path)
                ext_nodes, edges = _extract_python_imports(
                    f["path"], source_module, module_lookup, node_ids
                )
            else:
                source_node_id = rel_path.replace("/", ".").replace("\\", ".")
                ext_nodes, edges = _extract_js_imports(
                    f["path"], source_node_id, node_ids, file_node_map
                )

            nodes.extend(ext_nodes)
            all_edges.extend(edges)

        # ---- Step 4: Deduplicate edges ----
        seen: Set[Tuple[str, str]] = set()
        unique_edges: List[Dict] = []
        for e in all_edges:
            key = (e["source"], e["target"])
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)

        return {"nodes": nodes, "edges": unique_edges}

    except Exception as e:
        print(f"Warning: Failed to generate diagram: {e}")
        return {"nodes": [], "edges": []}
