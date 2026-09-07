"""Deterministic parity rule engine for ParityLens.

This module performs explainable, rule-based comparisons between an Urdu and an
English version of the same exam question. It is model-agnostic and can be unit
 tested in isolation.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz


@dataclasses.dataclass(frozen=True)
class Flag:
    category: str
    severity: str  # 'high', 'medium', 'low'
    message: str
    en_evidence: str
    ur_evidence: str
    confidence: float  # 0.0 - 1.0


# -----------------------------------------------------------------------------
# Normalisation helpers
# -----------------------------------------------------------------------------

def normalise(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    # Replace common Urdu digit variants with ASCII digits.
    text = text.replace("۰", "0").replace("۱", "1").replace("۲", "2")
    text = text.replace("۳", "3").replace("۴", "4").replace("۵", "5")
    text = text.replace("۶", "6").replace("۷", "7").replace("۸", "8").replace("۹", "9")
    # Normalise whitespace.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_diacritics(text: str) -> str:
    # Remove common Arabic/Urdu diacritics for robust keyword matching.
    diacritics = "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670"
    return "".join(c for c in text if c not in diacritics)


# -----------------------------------------------------------------------------
# Numbers
# -----------------------------------------------------------------------------

_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])"          # not preceded by alphanumerics (avoid H2O)
    r"-?\d+(?:\.\d+)?"
    r"(?![A-Za-z0-9])"           # not followed by alphanumerics
)


def extract_numbers(text: str) -> List[float]:
    nums = []
    for m in _NUMBER_RE.finditer(normalise(text)):
        try:
            nums.append(float(m.group()))
        except ValueError:
            continue
    return nums


def check_numbers(en: str, ur: str) -> List[Flag]:
    en_nums = extract_numbers(_question_stem(en))
    ur_nums = extract_numbers(_question_stem(ur))
    flags: List[Flag] = []
    if len(en_nums) != len(ur_nums):
        flags.append(
            Flag(
                category="Numeric mismatch",
                severity="high",
                message=f"Different number counts: English {len(en_nums)} vs Urdu {len(ur_nums)}",
                en_evidence=str(en_nums),
                ur_evidence=str(ur_nums),
                confidence=0.9,
            )
        )
    else:
        for i, (a, b) in enumerate(zip(en_nums, ur_nums)):
            if abs(a - b) > 1e-6:
                flags.append(
                    Flag(
                        category="Numeric mismatch",
                        severity="high",
                        message=f"Number mismatch #{i+1}: {a} (EN) vs {b} (UR)",
                        en_evidence=str(a),
                        ur_evidence=str(b),
                        confidence=0.95,
                    )
                )
    return flags


# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------

_UNITS_EN = [
    "kg", "g", "mg", "ton", "tons",
    "cm", "mm", "km",
    "sec", "min", "hr", "hour", "hours",
    "ml", "litre", "liter", "litres", "liters",
    "m/s", "km/h", "m/s^2", "m/s2", "m/s²",
    "N", "J", "W", "Pa", "kPa",
    "°C", "°F", "degree celsius", "degrees celsius",
    "ohm", "volts", "volt", "mol", "mole",
    # Single-letter units are only valid when adjacent to a number.
]

_UNITS_UR = [
    "کلوگرام", "گرام", "ملی گرام", "ٹن",
    "میٹر", "سینٹی میٹر", "ملی میٹر", "کلو میٹر",
    "سیکنڈ", "منٹ", "گھنٹہ", "گھنٹے",
    "لیٹر", "ملی لیٹر",
    "میٹر فی سیکنڈ", "کلومیٹر فی گھنٹہ",
    "ڈگری سیلسیس", "ڈگری فارنہائٹ", "کیلون",
    "نیوٹن", "جول", "واٹ", "پاسکل",
    "وولٹ", "امپیئر", "اہم", "مول",
]


_SINGLE_LETTER_UNITS_EN = {"m", "s", "l", "a", "k", "g", "n", "j", "w", "p"}


def _unit_context_ok(text: str, unit: str, start: int, end: int) -> bool:
    """Require single-letter units to be next to a digit or a math/compound marker."""
    if unit not in _SINGLE_LETTER_UNITS_EN:
        return True
    before = text[start - 1 : start] if start > 0 else ""
    after = text[end : end + 1] if end < len(text) else ""
    if before.isdigit() or after.isdigit():
        return True
    if after in {"/", "^", "²", "2"}:
        return True
    return False


def _en_unit_context_ok(text: str, start: int, end: int) -> bool:
    """Require unit to be a standalone token, not embedded in a word."""
    if start > 0 and text[start - 1].isalnum():
        return False
    if end < len(text) and text[end].isalpha():
        return False
    return True


def token_units_en(text: str) -> List[str]:
    norm = normalise(text).lower()
    found = []
    # Multi-letter / compound units.
    for unit in sorted(_UNITS_EN, key=len, reverse=True):
        unit_lower = unit.lower()
        start = 0
        while True:
            idx = norm.find(unit_lower, start)
            if idx == -1:
                break
            end = idx + len(unit_lower)
            if _unit_context_ok(norm, unit, idx, end) and _en_unit_context_ok(norm, idx, end):
                found.append(unit)
                norm = norm[:idx] + " " * len(unit_lower) + norm[end:]
            start = idx + len(unit_lower)
    return found


def _ur_unit_context_ok(text: str, start: int, end: int) -> bool:
    """Require Urdu unit to be a standalone token, not embedded in a word."""
    if start > 0:
        before = text[start - 1]
        if "\u0600" <= before <= "\u06FF" or before.isalnum():
            return False
    if end < len(text):
        after = text[end]
        if "\u0600" <= after <= "\u06FF" or after.isalpha():
            return False
    return True


def token_units_ur(text: str) -> List[str]:
    norm = strip_diacritics(normalise(text))
    found = []
    for unit in sorted(_UNITS_UR, key=len, reverse=True):
        start = 0
        while True:
            idx = norm.find(unit, start)
            if idx == -1:
                break
            end = idx + len(unit)
            if _ur_unit_context_ok(norm, idx, end):
                found.append(unit)
                norm = norm[:idx] + " " * len(unit) + norm[end:]
            start = idx + len(unit)
    return found


_UNIT_EQUIVALENCE: Dict[str, List[str]] = {
    "kg": ["کلوگرام"],
    "g": ["گرام"],
    "mg": ["ملی گرام"],
    "m": ["میٹر"],
    "cm": ["سینٹی میٹر"],
    "mm": ["ملی میٹر"],
    "km": ["کلو میٹر"],
    "s": ["سیکنڈ"],
    "sec": ["سیکنڈ"],
    "min": ["منٹ"],
    "hr": ["گھنٹہ", "گھنٹے"],
    "hour": ["گھنٹہ", "گھنٹے"],
    "hours": ["گھنٹہ", "گھنٹے"],
    "l": ["لیٹر"],
    "liter": ["لیٹر"],
    "litre": ["لیٹر"],
    "ml": ["ملی لیٹر"],
    "m/s": ["میٹر فی سیکنڈ"],
    "km/h": ["کلومیٹر فی گھنٹہ"],
    "°c": ["ڈگری سیلسیس"],
    "degree celsius": ["ڈگری سیلسیس"],
    "degrees celsius": ["ڈگری سیلسیس"],
    "°f": ["ڈگری فارنہائٹ"],
    "k": ["کیلون"],
    "n": ["نیوٹن"],
    "j": ["جول"],
    "w": ["واٹ"],
    "pa": ["پاسکل"],
    "volt": ["وولٹ"],
    "volts": ["وولٹ"],
    "a": ["امپیئر"],
    "mol": ["مول"],
    "mole": ["مول"],
}


def units_compatible(en_unit: str, ur_unit: str) -> bool:
    en_u = en_unit.lower()
    ur_u = strip_diacritics(ur_unit)
    if en_u == ur_u:
        return True
    for en_key, ur_vals in _UNIT_EQUIVALENCE.items():
        if en_u == en_key and ur_u in ur_vals:
            return True
        if ur_u in ur_vals:
            # check reverse
            if en_u == en_key:
                return True
    return False


def _question_stem(text: str) -> str:
    """Return text before the first answer option label."""
    # Find first occurrence of A) / B. / C: etc.
    m = re.search(r"\b[A-Ea-e][\.\)\:–\-]\s", text)
    if m:
        return text[: m.start()]
    return text


def check_units(en: str, ur: str) -> List[Flag]:
    en_units = token_units_en(_question_stem(en))
    ur_units = token_units_ur(_question_stem(ur))
    flags: List[Flag] = []

    if len(en_units) != len(ur_units):
        flags.append(
            Flag(
                category="Unit mismatch",
                severity="high",
                message=f"Different unit counts: English {en_units} vs Urdu {ur_units}",
                en_evidence=str(en_units),
                ur_evidence=str(ur_units),
                confidence=0.85,
            )
        )
        return flags

    for eu, uu in zip(en_units, ur_units):
        if not units_compatible(eu, uu):
            flags.append(
                Flag(
                    category="Unit mismatch",
                    severity="high",
                    message=f"Unit mismatch: '{eu}' (EN) vs '{uu}' (UR)",
                    en_evidence=eu,
                    ur_evidence=uu,
                    confidence=0.9,
                )
            )
    return flags


# -----------------------------------------------------------------------------
# Negation / polarity
# -----------------------------------------------------------------------------

_NEG_EN = ["not", "no", "never", "none", "except", "least", "only", "without"]
_NEG_UR = ["نہیں", "نہ", "بغیر", "علاوہ", "سوائے", "صرف", "کبھی نہیں"]


def count_negation_markers(text: str, markers: List[str]) -> int:
    """Count whole-word negation markers; avoid matches inside unrelated words."""
    text_norm = strip_diacritics(normalise(text)).lower()
    count = 0
    # Require the marker to be surrounded by non-alphanumeric / non-Urdu-script
    # boundaries so that e.g. Urdu "نہ" is not counted inside "آئینہ".
    boundary = r"(?<![\u0600-\u06FFa-zA-Z0-9])"
    end_boundary = r"(?![\u0600-\u06FFa-zA-Z0-9])"
    for marker in markers:
        pattern = boundary + re.escape(marker.lower()) + end_boundary
        count += len(re.findall(pattern, text_norm))
    return count


def check_negation(en: str, ur: str) -> List[Flag]:
    en_count = count_negation_markers(_question_stem(en), _NEG_EN)
    ur_count = count_negation_markers(_question_stem(ur), _NEG_UR)
    flags: List[Flag] = []
    if en_count != ur_count:
        flags.append(
            Flag(
                category="Negation/polarity mismatch",
                severity="high",
                message=f"Polarity marker count differs: English {en_count} vs Urdu {ur_count}",
                en_evidence=f"markers: {en_count}",
                ur_evidence=f"markers: {ur_count}",
                confidence=0.88,
            )
        )
    return flags


# -----------------------------------------------------------------------------
# Answer options
# -----------------------------------------------------------------------------

_OPTION_RE = re.compile(r"\b([A-Ea-e])[\.\)\:–\-]\s*(.+?)(?=\s+[A-Ea-e][\.\)\:–\-]|\Z)", re.DOTALL)


def extract_options(text: str) -> Dict[str, str]:
    text = normalise(text)
    # Strip leading question text by looking for first option-like occurrence.
    options = {}
    for label, body in _OPTION_RE.findall(text):
        options[label.upper()] = " ".join(body.split())
    # Fallback: simple line-by-line option detection.
    if not options:
        for line in text.split("\n"):
            line = line.strip()
            m = re.match(r"^([A-Ea-e])[\.\)\:]\s*(.+)$", line)
            if m:
                options[m.group(1).upper()] = " ".join(m.group(2).split())
    return options


def _option_overlap_score(en_opt: str, ur_opt: str) -> float:
    """Cross-lingual option similarity using bilingual keyword overlap.

    Imports from semantic lazily to avoid a circular import at module load.
    """
    from paritylens.engine.semantic import _BILINGUAL_KW, content_tokens

    en_tokens = content_tokens(en_opt, "en")
    if not en_tokens:
        return 0.0
    ur_text = strip_diacritics(normalise(ur_opt)).lower()
    matched = 0
    for et in en_tokens:
        if et in ur_text:
            matched += 1
        else:
            ur_equivs = _BILINGUAL_KW.get(et, set())
            if any(kw.lower() in ur_text for kw in ur_equivs):
                matched += 1
    return matched / len(en_tokens)


def _normalised_option(text: str) -> str:
    """Whitespace-collapsed, lowercased, diacritic-stripped option string."""
    t = strip_diacritics(normalise(text)).lower()
    return re.sub(r"\s+", "", t)


def _numeric_signature(text: str, lang: str = "en") -> Tuple[List[float], List[str]]:
    """Extract sorted numbers and units from an option for quick equality checks."""
    nums = sorted(extract_numbers(text))
    units = sorted(token_units_en(text) if lang == "en" else token_units_ur(text))
    return nums, units


def _option_similarity(en_opt: str, ur_opt: str) -> float:
    """Combined cross-lingual similarity for an option pair."""
    en_opt = en_opt.strip()
    ur_opt = ur_opt.strip()
    if not en_opt or not ur_opt:
        return 1.0 if en_opt == ur_opt else 0.0

    # Identical normalised strings (formulas, numbers, units) are a strong match.
    if _normalised_option(en_opt) == _normalised_option(ur_opt):
        return 1.0

    # Numeric options: if the numbers match, treat the options as aligned even
    # if units are expressed differently (unit mismatches are checked separately).
    en_nums, _ = _numeric_signature(en_opt, "en")
    ur_nums, _ = _numeric_signature(ur_opt, "ur")
    if en_nums and en_nums == ur_nums:
        return 0.95

    # Fallback: bilingual keyword overlap + weak phonetic fuzzy score.
    overlap = _option_overlap_score(en_opt, ur_opt)
    from paritylens.engine.semantic import urdu_to_latin
    en_lat = " ".join(re.findall(r"[a-z]+", en_opt.lower()))
    ur_lat = " ".join(urdu_to_latin(ur_opt).split())
    fuzzy = fuzz.token_sort_ratio(en_lat, ur_lat) / 100.0 if (en_lat and ur_lat) else 0.0
    return 0.75 * overlap + 0.25 * fuzzy


def check_options(en: str, ur: str) -> List[Flag]:
    en_opts = extract_options(en)
    ur_opts = extract_options(ur)
    flags: List[Flag] = []

    if len(en_opts) != len(ur_opts):
        flags.append(
            Flag(
                category="Answer-option mismatch or reordering",
                severity="high",
                message=f"Option count differs: English {len(en_opts)} vs Urdu {len(ur_opts)}",
                en_evidence=str(list(en_opts.keys())),
                ur_evidence=str(list(ur_opts.keys())),
                confidence=0.9,
            )
        )

    # Detect reordering first so that reordered options are not also spammed with
    # per-option content-mismatch flags.
    reordered_pair: Optional[Tuple[str, str]] = None
    if set(en_opts.keys()) == set(ur_opts.keys()) and len(en_opts) > 1:
        for label in en_opts:
            best_other_label = max(
                ur_opts.keys(),
                key=lambda l: _option_similarity(en_opts[label], ur_opts[l]),
            )
            if best_other_label != label:
                cur = _option_similarity(en_opts[label], ur_opts[label])
                other = _option_similarity(en_opts[label], ur_opts[best_other_label])
                if other > cur + 0.25:
                    reordered_pair = (label, best_other_label)
                    break

    reordered_labels = {reordered_pair[0], reordered_pair[1]} if reordered_pair else set()

    labels = sorted(set(en_opts.keys()) | set(ur_opts.keys()))
    for label in labels:
        e = en_opts.get(label, "")
        u = ur_opts.get(label, "")
        if not e or not u:
            continue
        # Compare content using cross-lingual overlap; only flag very large divergences.
        score = _option_similarity(e, u)
        if score < 0.2 and label not in reordered_labels:
            flags.append(
                Flag(
                    category="Answer-option mismatch or reordering",
                    severity="medium",
                    message=f"Option {label} content differs significantly (similarity {score:.2f})",
                    en_evidence=e[:120],
                    ur_evidence=u[:120],
                    confidence=round(1 - score, 2),
                )
            )

    if reordered_pair:
        a, b = reordered_pair
        flags.append(
            Flag(
                category="Answer-option mismatch or reordering",
                severity="medium",
                message=f"Possible option reordering around label {a}/{b}",
                en_evidence=f"{a}: {en_opts[a][:80]}",
                ur_evidence=f"{b}: {ur_opts[b][:80]}",
                confidence=round(
                    _option_similarity(en_opts[a], ur_opts[b])
                    - _option_similarity(en_opts[a], ur_opts[a]),
                    2,
                ),
            )
        )
    return flags


# -----------------------------------------------------------------------------
# Formulas / symbols
# -----------------------------------------------------------------------------

_FORMULA_RE = re.compile(r"[A-Z][a-z]?\d*|\d*[A-Z][a-z]?|\$[^$]+\$|\\\([^)]+\\\)|[\u2200-\u22FF]|[\u03B1-\u03C9]|[\u221A\u222B\u2248\u2260\u2264\u2265]")


_COMMON_WORDS = {
    "the", "he", "it", "at", "in", "on", "to", "of", "be", "is", "as", "an",
    "or", "if", "no", "so", "do", "we", "us", "my", "me", "by", "up", "go",
    "am", "pm", "co", "oh", "ha", "pa", "ma", "hi", "ho", "uh", "wh", "th",
    "si", "ha", "ke", "pe",
}

# Letter-only tokens that are valid formulas/symbols despite looking like words.
_FORMULA_WHITELIST = {
    "SI", "pH", "CO", "OH", "CH", "H2O", "CO2", "O2", "NaCl", "H2", "SO4",
    "NO3", "NH3", "HCl", "CaCO3", "KE", "PE", "IR", "UV", "DC", "AC", "V",
    "I", "R", "P", "F", "m", "a", "E", "mc", "mc2",
}


def _looks_like_formula(token: str) -> bool:
    """Keep token if it contains a digit, subscript, superscript, math symbol,
    Greek letter, or is a known letter-only formula."""
    if token in _FORMULA_WHITELIST:
        return True
    if any(c.isdigit() for c in token):
        return True
    if any(ord(c) in range(0x2070, 0x209F) or ord(c) in range(0x00B2, 0x00B4) for c in token):
        return True
    if any("\u2200" <= c <= "\u22FF" or "\u03B1" <= c <= "\u03C9" for c in token):
        return True
    return False


def extract_formulas(text: str) -> List[str]:
    # Very lightweight formula/symbol extraction.
    formulas = _FORMULA_RE.findall(normalise(text))
    # Filter out single uppercase letters, common words, and plain words that
    # do not look like formulas.
    formulas = [
        f for f in formulas
        if (len(f) > 1 or not f.isalpha())
        and f.lower() not in _COMMON_WORDS
        and _looks_like_formula(f)
    ]
    return formulas


def check_formulas(en: str, ur: str) -> List[Flag]:
    en_f = extract_formulas(_question_stem(en))
    ur_f = extract_formulas(_question_stem(ur))
    flags: List[Flag] = []
    if len(en_f) != len(ur_f):
        flags.append(
            Flag(
                category="Formula/symbol mismatch",
                severity="medium",
                message=f"Formula/symbol counts differ: English {len(en_f)} vs Urdu {len(ur_f)}",
                en_evidence=str(en_f),
                ur_evidence=str(ur_f),
                confidence=0.75,
            )
        )
    return flags


# -----------------------------------------------------------------------------
# Named entities (lightweight)
# -----------------------------------------------------------------------------


def extract_named_entities(text: str) -> List[str]:
    # Heuristic: capitalised phrases in English; ignore sentence starts.
    norm = normalise(text)
    entities = []
    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", norm):
        phrase = match.group(1)
        if phrase.lower() not in {"the", "a", "an"}:
            entities.append(phrase)
    return entities


def check_named_entities(en: str, ur: str) -> List[Flag]:
    en_ent = extract_named_entities(_question_stem(en))
    ur_ent = extract_named_entities(_question_stem(ur))
    flags: List[Flag] = []
    if len(en_ent) != len(ur_ent):
        flags.append(
            Flag(
                category="Named-entity mismatch",
                severity="low",
                message=f"Named entity counts differ: English {len(en_ent)} vs Urdu {len(ur_ent)}",
                en_evidence=str(en_ent),
                ur_evidence=str(ur_ent),
                confidence=0.6,
            )
        )
    return flags


# -----------------------------------------------------------------------------
# Missing condition / constraint
# -----------------------------------------------------------------------------

_CONDITION_MARKERS_EN = ["if", "when", "given that", "provided", "assuming", "unless", "because"]
_CONDITION_MARKERS_UR = ["اگر", "جب", "یہ دیکھتے ہوئے", "فرض کریں", "جب تک", "کیونکہ"]


def check_conditions(en: str, ur: str) -> List[Flag]:
    en_c = sum(1 for m in _CONDITION_MARKERS_EN if m.lower() in normalise(_question_stem(en)).lower())
    ur_c = sum(1 for m in _CONDITION_MARKERS_UR if strip_diacritics(m) in strip_diacritics(normalise(_question_stem(ur))))
    flags: List[Flag] = []
    if abs(en_c - ur_c) >= 2:
        flags.append(
            Flag(
                category="Missing condition or constraint",
                severity="medium",
                message=f"Condition/constraint marker counts differ sharply: English {en_c} vs Urdu {ur_c}",
                en_evidence=f"markers: {en_c}",
                ur_evidence=f"markers: {ur_c}",
                confidence=0.65,
            )
        )
    return flags


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------

def run_deterministic_checks(en: str, ur: str) -> List[Flag]:
    """Run all deterministic rules and return a flat list of flags."""
    checks = [
        check_numbers,
        check_units,
        check_negation,
        check_options,
        check_formulas,
        check_named_entities,
        check_conditions,
    ]
    flags: List[Flag] = []
    for check in checks:
        try:
            flags.extend(check(en, ur))
        except Exception:
            # Rule engine must never crash the pipeline.
            continue
    return flags
