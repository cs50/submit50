"""Consistency checks for the gettext catalogs under submit50/locale."""
import ast
import gettext
import io
import pathlib
import re

import pytest
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "submit50" / "__main__.py"
LOCALE_DIR = ROOT / "submit50" / "locale"
LOCALES = sorted(p.name for p in LOCALE_DIR.iterdir() if (p / "LC_MESSAGES" / "submit50.po").is_file())

# Catalogs known to be incomplete before the completeness check existed.
KNOWN_INCOMPLETE = {"es"}


def source_strings():
    """Every string literal passed to _() in __main__.py."""
    literals = set()
    for node in ast.walk(ast.parse(SOURCE.read_text())):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            literals.add(node.args[0].value)
    assert literals, "no _() literals found -- extraction is broken"
    return literals


def load_po(locale):
    with open(LOCALE_DIR / locale / "LC_MESSAGES" / "submit50.po", "rb") as f:
        return read_po(f, locale=locale)


@pytest.mark.parametrize("locale", LOCALES)
def test_every_source_string_is_translated(locale, request):
    if locale in KNOWN_INCOMPLETE:
        request.applymarker(pytest.mark.xfail(reason=f"{locale} catalog is known to be incomplete", strict=True))
    catalog = load_po(locale)
    translations = {m.id: m.string for m in catalog if m.id}
    missing = sorted(s for s in source_strings() if s not in translations)
    empty = sorted(s for s in source_strings() if s in translations and not translations[s])
    fuzzy = sorted(m.id for m in catalog if m.id and m.fuzzy)
    assert not missing, f"{locale}: strings missing from catalog: {missing}"
    assert not empty, f"{locale}: untranslated strings: {empty}"
    assert not fuzzy, f"{locale}: fuzzy entries are skipped by compile_catalog: {fuzzy}"


@pytest.mark.parametrize("locale", LOCALES)
def test_prompt_translations_keep_trailing_space(locale):
    """input() prompts end with a space in the source; a translation that drops it glues the cursor to the text."""
    for message in load_po(locale):
        if message.id and message.string and message.id.endswith(" "):
            assert message.string.endswith(" "), f"{locale}: translation of {message.id!r} lost its trailing space"


@pytest.mark.parametrize("locale", LOCALES)
def test_yes_regex_translation_is_valid(locale):
    """`y|yes` is interpolated into a regex; the translation must compile and accept its own affirmative."""
    catalog = load_po(locale)
    translated = catalog.get("y|yes")
    if translated is None or not translated.string:
        pytest.skip(f"{locale}: y|yes not translated")
    pattern = re.compile(rf"^\s*(?:{translated.string})\s*$", re.I)
    first_alternative = translated.string.split("|")[0]
    assert pattern.match(first_alternative), f"{locale}: regex rejects its own first alternative"
    assert not pattern.match("no"), f"{locale}: regex accepts 'no'"


@pytest.mark.parametrize("locale", LOCALES)
def test_committed_mo_matches_po(locale):
    """A committed .mo must be the compiled form of the committed .po (`*.mo` is gitignored, so it drifts silently)."""
    mo_path = LOCALE_DIR / locale / "LC_MESSAGES" / "submit50.mo"
    if not mo_path.is_file():
        pytest.skip(f"{locale}: no .mo committed (CI compiles it at build time)")
    buf = io.BytesIO()
    write_mo(buf, load_po(locale))
    expected = gettext.GNUTranslations(io.BytesIO(buf.getvalue()))._catalog
    with open(mo_path, "rb") as f:
        actual = gettext.GNUTranslations(f)._catalog
    expected.pop("", None)
    actual.pop("", None)
    assert actual == expected, f"{locale}: submit50.mo is stale -- run `python setup.py compile_catalog` and recommit"
