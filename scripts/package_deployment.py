"""Package only runtime source, sample data and compiled React; never environment files."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent


def package(output: Path = ROOT / "deployment.zip") -> None:
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Build React first: cd frontend && npm ci && npm run build")
    files = [ROOT / "requirements.lock", ROOT / "azure-startup.sh"]
    files += list((ROOT / "crunch_week").glob("*.py"))
    files += list((ROOT / "sample_data").glob("*.pdf"))
    files += list((ROOT / "sample_data").glob("*.txt"))
    files += [path for path in (ROOT / "frontend/dist").rglob("*") if path.is_file()]
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("requirements.txt", "-r requirements.lock\n")
        for path in sorted(files):
            # Defensive filename-only check before reading any runtime/build file.
            if path.name.lower().startswith(".env") or path.name.lower() in {"env", "env.example"}:
                continue
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Created {output.name} with the backend, compiled frontend and pinned runtime dependencies.")


if __name__ == "__main__":
    package()
