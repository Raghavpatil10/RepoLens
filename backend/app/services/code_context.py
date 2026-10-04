from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

def get_code_context(
    repo_path: Path,
    file_path: str,
    line_number: int,
    func_start_line: Optional[int] = None,
    func_end_line: Optional[int] = None,
) -> Optional[Dict]:
    """
    Reads the source file and extracts the relevant code context.
    Returns a dictionary containing start_line, end_line, highlight_line,
    and a list of lines with their content and highlight boolean.
    """
    full_path = (repo_path / file_path).resolve()

    # Prevent path traversal
    if not str(full_path).startswith(str(repo_path.resolve())):
        return None

    try:
        if not full_path.is_file():
            return None
        
        # Read the file contents
        content = full_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        
        if not lines:
            return None
            
        total_lines = len(lines)
        
        if func_start_line is not None and func_end_line is not None:
            # We have a specific function boundary
            start = max(1, func_start_line)
            end = min(total_lines, func_end_line)
        else:
            # Fall back to +/- 5 lines
            start = max(1, line_number - 5)
            end = min(total_lines, line_number + 5)
            
        context_lines = []
        for i in range(start, end + 1):
            # 1-indexed to 0-indexed
            line_content = lines[i - 1]
            context_lines.append({
                "number": i,
                "code": line_content,
                "highlight": (i == line_number)
            })
            
        return {
            "start_line": start,
            "end_line": end,
            "highlight_line": line_number,
            "lines": context_lines
        }
    except Exception:
        # Failsafe for unreadable files
        return None
