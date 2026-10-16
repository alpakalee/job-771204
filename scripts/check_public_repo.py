from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIMIT_BYTES = 128 * 1024 * 1024
EXCLUDED_PARTS = {
    ".git",
    ".secrets",
    ".venv",
    "__pycache__",
    "artifacts",
    "docs",
    "dist",
    "integration_tests",
    "node_modules",
    "repro",
    "solver",
    "tests",
}

REQUIRED_PATHS = (
    "wargame/Description.md",
    "wargame/public",
)
REQUIRED_IGNORES = {
    "docs/",
    "integration_tests/",
    "repro/",
    "solver/",
    "scripts/build_dreamhack_package.py",
    "wargame/.dockerignore",
    "wargame/Dockerfile",
    "wargame/Specfile",
    "wargame/requirements.txt",
    "wargame/server/",
    "wargame/server/tests/",
    "dist/",
    ".secrets/",
}
EXCLUDED_RELATIVE = {
    "scripts/build_dreamhack_package.py",
    "wargame/.dockerignore",
    "wargame/Dockerfile",
    "wargame/Specfile",
    "wargame/requirements.txt",
}


def included_files() -> list[Path]:
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if (
            path.is_file()
            and relative.as_posix() not in EXCLUDED_RELATIVE
            and not any(part in EXCLUDED_PARTS for part in relative.parts)
        ):
            result.append(path)
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    for relative in REQUIRED_PATHS:
        require((ROOT / relative).exists(), f"missing {relative}")

    ignore_lines = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing_ignores = sorted(REQUIRED_IGNORES - ignore_lines)
    require(not missing_ignores, f"missing sensitive .gitignore entries: {missing_ignores}")

    public_files = sorted(path for path in (ROOT / "wargame" / "public").rglob("*") if path.is_file())
    require(bool(public_files), "wargame/public is empty")

    private_key_markers = tuple(
        b"-----BEGIN " + key_type + b"PRIVATE KEY-----"
        for key_type in (b"", b"RSA ", b"EC ", b"DSA ", b"ENCRYPTED ")
    )
    for path in included_files():
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SystemExit(f"FAIL: cannot read {path}: {exc}") from exc
        require(
            not any(marker in data for marker in private_key_markers),
            f"private key PEM in {path.relative_to(ROOT)}",
        )

    private_suffixes = {".key", ".p12", ".pfx"}
    leaked_names = sorted(path.name for path in public_files if path.suffix.lower() in private_suffixes)
    require(not leaked_names, f"private key container in public/: {leaked_names}")

    files = included_files()
    total_bytes = sum(path.stat().st_size for path in files)
    require(total_bytes < LIMIT_BYTES, "public repository exceeds Dreamhack's 128 MiB limit")

    result = {
        "status": "PASS",
        "included_files": len(files),
        "included_mib": round(total_bytes / 1024 / 1024, 3),
        "public_files": len(public_files),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

