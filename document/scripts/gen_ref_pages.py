"""Generate MkDocs API reference pages from Python modules under source/."""

from pathlib import Path

import mkdocs_gen_files


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "source"
REFERENCE_ROOT = Path("reference")


def module_parts(path: Path) -> tuple[str, ...]:
    relative = path.relative_to(SOURCE_ROOT).with_suffix("")
    if relative.name == "__init__":
        relative = relative.parent
    return tuple(relative.parts)


nav = mkdocs_gen_files.Nav()
python_files = sorted(SOURCE_ROOT.rglob("*.py")) if SOURCE_ROOT.exists() else []
documented_modules = 0

with mkdocs_gen_files.open(REFERENCE_ROOT / "index.md", "w") as index_file:
    print("# API Reference", file=index_file)
    print("", file=index_file)
    print("This page is generated from Python docstrings under `source/`.", file=index_file)

for path in python_files:
    parts = module_parts(path)
    if not parts:
        continue

    module_name = ".".join(parts)
    doc_path = REFERENCE_ROOT.joinpath(*parts).with_suffix(".md")
    if path.name == "__init__.py":
        doc_path = REFERENCE_ROOT.joinpath(*parts, "index.md")

    nav[parts] = doc_path.relative_to(REFERENCE_ROOT).as_posix()

    with mkdocs_gen_files.open(doc_path, "w") as doc_file:
        print(f"# `{module_name}`", file=doc_file)
        print("", file=doc_file)
        print(f"::: {module_name}", file=doc_file)

    mkdocs_gen_files.set_edit_path(doc_path, Path("..") / path.relative_to(REPO_ROOT))
    documented_modules += 1

with mkdocs_gen_files.open(REFERENCE_ROOT / "SUMMARY.md", "w") as nav_file:
    if documented_modules:
        nav_file.writelines(nav.build_literate_nav())
    else:
        print("* [API Reference](index.md)", file=nav_file)
