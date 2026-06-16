"""Regenerate ``src/tessera_memory/models.py`` from the vendored ``openapi.json``.

CI runs this and `git diff --exit-code` to fail on a stale spec.

    uv run python scripts/generate_models.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi.json"
OUTPUT = ROOT / "src" / "tessera_memory" / "models.py"

FLAGS = [
    "--input",
    str(SPEC),
    "--input-file-type",
    "openapi",
    "--output",
    str(OUTPUT),
    "--output-model-type",
    "pydantic_v2.BaseModel",
    "--target-python-version",
    "3.10",
    "--use-standard-collections",
    "--use-union-operator",
    "--field-constraints",
    "--snake-case-field",
    "--use-schema-description",
    # Deterministic output: drop the generation timestamp (else the file changes on every
    # run and the model-drift check never passes) and pin formatters across versions.
    "--disable-timestamp",
    "--formatters",
    "black",
    "isort",
]


def _command() -> list[str]:
    if shutil.which("datamodel-codegen"):
        return ["datamodel-codegen", *FLAGS]
    return ["uvx", "--from", "datamodel-code-generator", "datamodel-codegen", *FLAGS]


def main() -> int:
    if not SPEC.exists():
        print(f"missing spec: {SPEC} (run `make sync-spec`)", file=sys.stderr)
        return 1
    cmd = _command()
    print("running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
