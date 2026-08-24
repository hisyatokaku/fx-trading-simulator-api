"""Extract code cells from a .ipynb notebook into a .py file.

Usage:
    python scripts/extract_ipynb_code.py <notebook.ipynb> [output.py]

If output.py is omitted, writes to /tmp/<notebook_name>.py
"""

import json
import sys
from pathlib import Path


def extract_code(notebook_path: Path) -> str:
    with notebook_path.open(encoding="utf-8") as f:
        notebook = json.load(f)

    chunks = []
    for i, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        # Comment out Jupyter magics (%...) and shell commands (!...)
        # so the output is valid Python
        lines = [
            f"# {line}" if line.lstrip().startswith(("%", "!")) else line
            for line in source.rstrip().splitlines()
        ]
        chunks.append(f"# %% [cell {i}]\n" + "\n".join(lines) + "\n")

    return "\n\n".join(chunks) + "\n"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    notebook_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = Path("/tmp") / (notebook_path.stem + ".py")

    output_path.write_text(extract_code(notebook_path), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
