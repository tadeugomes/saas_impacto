"""Gera SDKs (Python/TypeScript) a partir do schema OpenAPI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which

from app.config import get_settings


def run_command(command: list[str]) -> int:
    """Executa comando no shell e retorna código de saída."""
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def main() -> int:
    settings = get_settings()
    output_dir = Path(__file__).parent.parent / "sdk"
    output_dir.mkdir(parents=True, exist_ok=True)
    spec_url = "http://localhost:8000/openapi.json"

    if which("openapi-python-client"):
        status = run_command(
            [
                "openapi-python-client",
                "generate",
                "--url",
                spec_url,
                "--path",
                str(output_dir / "python"),
                "--meta",
                "false",
            ]
        )
        if status != 0:
            print("Falha ao gerar SDK Python.")
            return status
    else:
        print("openapi-python-client não encontrado. Instale em ambiente de release.")

    if which("openapi-typescript-codegen"):
        return run_command(
            [
                "openapi-typescript-codegen",
                "--input",
                spec_url,
                "--output",
                str(output_dir / "typescript"),
            ]
        )

    print("openapi-typescript-codegen não encontrado. Instale em ambiente de release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
