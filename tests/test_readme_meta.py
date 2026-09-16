"""Claims the repository makes about itself.

The claim tests catch a figure that moved. They cannot catch a test count that drifted, a module
table that no longer matches the package, a README that lost its other language, or a placeholder
left in the text - and in the sibling repository two defects of exactly that class reached the
remote before this file existed there.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = ("TODO", "FIXME", "XXX", "TKTK", "LOREM", "_EN", "_PT")


def markdown_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.md")
        if not any(part.startswith(".") or part == "node_modules" for part in path.parts)
    ]


def collected(marker: str) -> int:
    """Tests pytest collects under a marker. There is no total line, so the per-file counts sum."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-m",
            marker,
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return sum(int(match) for match in re.findall(r"^\S+\.py:\s*(\d+)$", result.stdout, re.M))


def test_no_placeholder_tokens_survive_in_any_markdown() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}: {token}"
        for path in markdown_files()
        for token in PLACEHOLDERS
        if token in path.read_text(encoding="utf-8")
    ]
    assert not offenders, "placeholder tokens left in documentation: " + "; ".join(offenders)


def test_both_readmes_quote_the_number_of_tests_that_exist() -> None:
    """A count corrected in one language and not the other is the same bug."""
    fast = collected("not slow")
    total = fast + collected("slow")

    english = (ROOT / "README.md").read_text(encoding="utf-8")
    portuguese = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")

    quoted = {
        "English total": re.search(r"\*\*(\d[\d,]*) tests,", english),
        "English fast": re.search(r"(\d[\d,]*)\s+of\s+them\s+run\s+in", english),
        "Portuguese total": re.search(r"\*\*(\d[\d,]*) testes,", portuguese),
        "Portuguese fast": re.search(r"(\d[\d,]*)\s+deles\s+rodam\s+em", portuguese),
    }
    for label, match in quoted.items():
        assert match is not None, f"could not find the {label} test count in the README"

    assert int(quoted["English total"].group(1).replace(",", "")) == total
    assert int(quoted["English fast"].group(1).replace(",", "")) == fast
    assert int(quoted["Portuguese total"].group(1).replace(",", "")) == total
    assert int(quoted["Portuguese fast"].group(1).replace(",", "")) == fast

    # And the remainder is quoted as the slow count, in both languages. The patterns tolerate
    # line breaks, because Markdown wraps prose and a sentence can straddle two lines.
    slow = total - fast
    assert re.search(rf"remaining\s+{slow}\s+re-derive", english), "English slow count"
    assert re.search(rf"Os\s+{slow}\s+restantes\s+re-derivam", portuguese), "Portuguese slow count"


def test_the_module_table_matches_the_package() -> None:
    """A table listing a module that does not exist, or missing one that does, is a lie."""
    packages = {
        path.parent.name
        for path in (ROOT / "src" / "dmaic").rglob("__init__.py")
        if path.parent.name not in {"dmaic", "synth"}
    }
    for readme in ("README.md", "README.pt-BR.md"):
        text = (ROOT / readme).read_text(encoding="utf-8")
        listed = set(re.findall(r"\[`dmaic\.(\w+)`\]", text))
        assert listed == packages, f"{readme}: table lists {listed}, package has {packages}"


def test_every_module_readme_is_bilingual() -> None:
    """One language edition going stale is the failure mode, so both are required to exist."""
    for readme in (ROOT / "src" / "dmaic").rglob("README.md"):
        text = readme.read_text(encoding="utf-8")
        assert "*[Português]" in text, f"{readme.relative_to(ROOT)} has no Portuguese section link"
        assert "*[English]" in text, f"{readme.relative_to(ROOT)} has no English section link"
        assert "## Assumptions and limitations" in text, readme.relative_to(ROOT)
        assert "## Premissas e limitações" in text, readme.relative_to(ROOT)


def test_every_example_is_linked_from_both_readmes() -> None:
    """An example nothing references is an example nobody runs."""
    scripts = {path.name for path in (ROOT / "examples").glob("*.py")}
    for readme in ("README.md", "README.pt-BR.md"):
        text = (ROOT / readme).read_text(encoding="utf-8")
        for script in scripts:
            assert script in text, f"{readme} does not link examples/{script}"


def test_the_disclaimer_is_bilingual_and_names_the_invented_labels() -> None:
    """It is the load-bearing document of the repository, so its contract is tested."""
    text = (ROOT / "DISCLAIMER.md").read_text(encoding="utf-8")
    assert "# Disclaimer" in text
    assert "# Aviso" in text
    for label in ("BALANCA-01", "PAQUIMETRO-02", "INSPECAO-03"):
        assert label in text, f"{label} is not declared as an invented label"
