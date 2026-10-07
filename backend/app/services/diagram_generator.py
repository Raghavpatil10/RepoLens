import ast
from pathlib import Path
from typing import Dict, List, Set, Any


def generate_diagram(repo_path: Path, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = []
    edges = []
    
    # Track created node IDs to avoid duplicates
    node_ids: Set[str] = set()
    
    # 1. Create nodes for all discovered python files
    for f in files:
        if f.get("language") != "Python":
            continue
            
        rel_path = str(f["path"].relative_to(repo_path))
        module_name = rel_path.replace(".py", "").replace("/", ".")
        
        node_id = module_name
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": rel_path.split("/")[-1],
                "type": "file",
                "group": str(f["path"].parent.relative_to(repo_path)) if f["path"].parent != repo_path else "root"
            })
            node_ids.add(node_id)
            
    # 2. Extract imports to build edges
    for f in files:
        if f.get("language") != "Python":
            continue
            
        rel_path = str(f["path"].relative_to(repo_path))
        source_node_id = rel_path.replace(".py", "").replace("/", ".")
        
        try:
            source = f["path"].read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target_node_id = alias.name
                        # Only add edge if target is in our project nodes
                        if target_node_id in node_ids:
                            edges.append({
                                "source": source_node_id,
                                "target": target_node_id,
                                "label": "imports"
                            })
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        target_module = node.module
                        
                        # Handle relative imports roughly (assume absolute for simplicity if no level)
                        if node.level > 0:
                            parts = source_node_id.split(".")
                            if len(parts) >= node.level:
                                base = ".".join(parts[:-node.level])
                                if base:
                                    target_module = f"{base}.{target_module}"
                                    
                        if target_module in node_ids:
                            edges.append({
                                "source": source_node_id,
                                "target": target_module,
                                "label": "imports"
                            })
                            
                        # Also check if imported names are modules (e.g. from models import Diagram)
                        for alias in node.names:
                            target_node_id = f"{target_module}.{alias.name}"
                            if target_node_id in node_ids:
                                edges.append({
                                    "source": source_node_id,
                                    "target": target_node_id,
                                    "label": "imports"
                                })
        except Exception:
            pass

    return {
        "nodes": nodes,
        "edges": edges
    }
