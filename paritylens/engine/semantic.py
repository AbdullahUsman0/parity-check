"""Semantic equivalence scorer for ParityLens.

This prototype uses a lightweight, deterministic heuristic (normalisation,
transliteration, keyword overlap, fuzzy similarity) instead of a heavy
multilingual embedding model so the demo runs instantly. The interface is
swappable: drop in `sentence-transformers` or an API call later without
touching the rest of the pipeline.
"""

from __future__ import annotations

import re
from typing import Dict, List

from rapidfuzz import fuzz

from paritylens.engine.rules import _question_stem, normalise, strip_diacritics


# Simple Urdu -> Latin mapping for crude cross-lingual token overlap.
_URDU_LATIN = {
    "ا": "a", "آ": "aa", "ب": "b", "پ": "p", "ت": "t", "ٹ": "t", "ث": "s",
    "ج": "j", "چ": "ch", "ح": "h", "خ": "kh", "د": "d", "ڈ": "d", "ذ": "z",
    "ر": "r", "ڑ": "r", "ز": "z", "ژ": "zh", "س": "s", "ش": "sh", "ص": "s",
    "ض": "z", "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "q",
    "ک": "k", "گ": "g", "ل": "l", "م": "m", "ن": "n", "ں": "n", "و": "o",
    "ہ": "h", "ھ": "h", "ی": "i", "ے": "e", "ء": "a",
}

_STOPWORDS_EN = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "and", "but", "or", "yet", "so", "if",
    "because", "although", "though", "while", "where", "when", "that",
    "which", "who", "whom", "whose", "this", "these", "those",
}

_STOPWORDS_UR = {
    "کا", "کی", "کے", "میں", "سے", "پر", "نے", "بھی", "ہے", "ہیں", "تھا",
    "تھی", "تھے", "اور", "کہ", "کو", "کیونکہ", "اگر", "جب", "تک", "جیسا",
    "وہ", "یہ", "جن", "جو", "جس", "ان", "انہوں", "تم", "ہم", "آپ",
}

# Bilingual keyword map: English term -> set of Urdu-script equivalents.
# Used to boost semantic overlap for aligned translated content.
_BILINGUAL_KW: Dict[str, set] = {
    # Physics quantities
    "force": {"قوہ", "قوت"},
    "energy": {"توانائی"},
    "power": {"واٹ", "توانائی"},
    "work": {"کام"},
    "mass": {"کمیت", "وزن"},
    "weight": {"وزن"},
    "speed": {"رفتار"},
    "velocity": {"رفتار", "سمتاررفتار"},
    "displacement": {"اداریہ", "ادارتیہ"},
    "acceleration": {"اسراع", "سعت"},
    "distance": {"فاصلہ"},
    "time": {"وقت"},
    "current": {"امپیئر", "برقی", "رو"},
    "voltage": {"وولٹ"},
    "resistance": {"مزاحمت", "اہم"},
    "pressure": {"پاسکل", "دباؤ"},
    "temperature": {"حرارت", "درجہ"},
    "potential": {"صَلاحیت", "صLagat"},
    "kinetic": {"حرکی"},
    # Electrical units
    "ampere": {"امیئر", "امپیئر"},
    "volt": {"وولٹ"},
    "voltage": {"وولٹ"},
    "ohm": {"اہم"},
    "watt": {"واٹ"},
    "joule": {"جول"},
    "pascal": {"پاسکل"},
    # Mirror / lens
    "convex": {"قوسی دور"},
    "concave": {"قوسی"},
    "plane": {"سطحی"},
    "mirror": {"آئینہ"},
    "lens": {"عدسہ"},
    # Organelles
    "mitochondria": {"مائٹوکونڈریا"},
    "ribosome": {"رائیبوزوم"},
    "nucleus": {"نیوکلس"},
    "chloroplast": {"کلوروپلاسٹ"},
    # Ordinal / law
    "first": {"پہلا"},
    "second": {"دوسرا"},
    "third": {"تیسرا"},
    "gravitation": {"کشش ثقل"},
    # Common option verbs
    "fight": {"لڑنا"},
    "clot": {"جمنا"},
    "dioxide": {"ڈائی آکسائیڈ"},
    # Answer-only tokens
    "none": {"کوئی نہیں", "کچھ نہیں"},
    "all": {"تمام", "سب"},
    # Matter
    "atom": {"ایٹم"},
    "molecule": {"سالمہ"},
    "electron": {"الیکٹرون"},
    "proton": {"پروٹون"},
    "neutron": {"نیوٹرون"},
    "oxygen": {"آکسیجن"},
    "hydrogen": {"ہائیڈروجن"},
    "nitrogen": {"نیٹروجن"},
    "carbon": {"کاربن"},
    "water": {"پانی"},
    "gas": {"گیس"},
    "liquid": {"مایع"},
    "solid": {"جامد"},
    "metal": {"دھات"},
    "acid": {"تیزاب"},
    "base": {"قارو"},
    "salt": {"نمک"},
    # Biology
    "cell": {"سیل"},
    "organelle": {"عضیہ"},
    "organ": {"عضو"},
    "blood": {"خون"},
    "heart": {"دل"},
    "lung": {"پھیپھڑا"},
    "kidney": {"گردہ", "گردے"},
    "brain": {"دماغ"},
    "plant": {"پودا"},
    "animal": {"جانور"},
    "pancreas": {"پینکریاز"},
    "insulin": {"انسولین"},
    "glucose": {"گلوکوز"},
    "oxygen": {"آکسیجن"},
    # Phenomena
    "light": {"روشنی"},
    "sound": {"آواز"},
    "heat": {"گرمی"},
    "mirror": {"آئینہ"},
    "lens": {"عدسہ"},
    "sun": {"سورج"},
    "earth": {"زمین"},
    "moon": {"چاند"},
    "star": {"ستارہ"},
    "planet": {"سیارہ"},
    "vacuum": {"خلا"},
    # Processes
    "photosynthesis": {"فوٹو", "فوٹو سنتیسز"},
    "chlorophyll": {"کلوروفل"},
    "refraction": {"انحراف"},
    "evaporation": {"بخارات", "بخار"},
    "condensation": {"میعان"},
    "respiration": {"سانس"},
    "digestion": {"ہضم"},
    "circulation": {"دوران"},
    # Geometry / measurement
    "circle": {"دائرہ", "دائرے"},
    "radius": {"رداس"},
    "area": {"رقبہ", "مساحت"},
    "triangle": {"مثلث"},
    "angle": {"زاویہ", "زاویوں"},
    "angles": {"زاویہ", "زاویوں"},
    "sum": {"مجموعہ"},
    "volume": {"حجم"},
    "length": {"لمبائی"},
    "right": {"قائمہ", "دائیں", "صحیح"},
    "angled": {"زاویہ"},
    "other": {"دیگر"},
    "two": {"دو"},
    # Common exam vocabulary
    "unit": {"یونٹ"},
    "si": {"si"},
    "formula": {"فارمولا"},
    "chemical": {"کیمیائی"},
    "equation": {"مساوات"},
    "value": {"قیمت"},
    "number": {"نمبر", "تعداد"},
    "calculate": {"نکالیں", "حساب"},
    "define": {"تعریف"},
    "function": {"کام"},
    "role": {"کردار"},
    "process": {"عمل"},
    "change": {"تبدیل", "تبدیلی"},
    "convert": {"تبدیل"},
    "absorb": {"جذب"},
    "release": {"خارج"},
    "store": {"ذخیرہ"},
    "transport": {"منتقل"},
    "produce": {"بناتا", "بنانا", "پیدا"},
    "make": {"بناتا", "بنانا"},
    "pump": {"پمپ"},
    "filter": {"فلٹر"},
    "form": {"بناتا"},
    "move": {"چل", "حرکت"},
    "moving": {"چل"},
    "constant": {"مستقل"},
    "rest": {"سکون"},
    "final": {"آخری"},
    "initial": {"ابتدائی"},
    "total": {"کل"},
    "average": {"اوسط"},
    "approximately": {"تقریباً"},
    "equal": {"برابر"},
    "opposite": {"مخالف"},
    "action": {"عمل"},
    "reaction": {"ردعمل"},
    "law": {"قانون"},
    "state": {"کہتا"},
    "always": {"ہمیشہ"},
    "virtual": {"مجازی"},
    "erect": {"سیدھی"},
    "diminished": {"چھوٹی"},
    "image": {"تصویر"},
    "body": {"جسم"},
    "human": {"انسانی"},
    "adult": {"بالغ"},
    "following": {"مندرجہ ذیل"},
    "which": {"کونسا", "کونسی"},
    "what": {"کیا"},
    "how": {"کتنا", "کتنی", "کیسے"},
    "many": {"کتنے", "کتنی"},
    "much": {"کتنا", "کتنی"},
    "why": {"کیوں"},
    "where": {"کہاں"},
    "when": {"کب"},
    "not": {"نہیں"},
    "known": {"کہا جاتا"},
    "called": {"کہا جاتا", "کہلاتا"},
    "essential": {"ضروری"},
    "pure": {"خالص"},
    "most": {"سب سے"},
    "abundant": {"زیادہ"},
    "atmosphere": {"فضا"},
    "skin": {"جلد"},
    "sunlight": {"دھوپ"},
    "vitamin": {"وٹامن"},
    "bones": {"ہڈیاں"},
    "infection": {"انفیکشن"},
    "antibodies": {"اینٹی باڈیز"},
    "valency": {"قیمتیہ"},
    # Options / answers
    "true": {"صحیح"},
    "false": {"غلط"},
    "correct": {"درست"},
    "incorrect": {"غلط"},
    # Planets
    "mercury": {"عطارد"},
    "venus": {"زہرہ"},
    "mars": {"مریخ"},
    "jupiter": {"مشتری"},
    "saturn": {"زحل"},
    "uranus": {"یورینس"},
    "neptune": {"نیپچون"},
    # Scientists / entities
    "newton": {"نیوٹن"},
    "einstein": {"آئنسٹائن"},
    "galileo": {"گلیلیو"},
    "aristotle": {"ارسطو"},
    "rutherford": {"رutherford", "رتھرفورڈ"},
    "bohr": {"بوہر"},
    "dalton": {"دالتن"},
    "thomson": {"تھامسن"},
}


def urdu_to_latin(text: str) -> str:
    text = strip_diacritics(normalise(text))
    out = []
    for ch in text:
        out.append(_URDU_LATIN.get(ch, ch))
    return "".join(out)


def content_tokens(text: str, lang: str = "en") -> List[str]:
    if lang == "ur":
        norm = strip_diacritics(normalise(text))
        tokens = re.findall(r"[\u0600-\u06FF]+", norm)
        stops = _STOPWORDS_UR
    else:
        norm = normalise(text).lower()
        tokens = re.findall(r"[a-z]+", norm)
        stops = _STOPWORDS_EN
    return [t for t in tokens if t not in stops and len(t) > 1]


def semantic_similarity(en: str, ur: str) -> Dict[str, float]:
    """Return similarity and confidence scores.

    Similarity is on [0, 1]; confidence reflects how much evidence the scorer
    had to work with (more tokens -> higher confidence, capped).
    """
    # Compare question stems only; options are handled by deterministic rules
    # and would otherwise dominate / distort semantic drift detection.
    en_stem = _question_stem(en)
    ur_stem = _question_stem(ur)

    en_tokens = content_tokens(en_stem, "en")
    ur_tokens = content_tokens(ur_stem, "ur")

    # Fuzzy score on Latin transliteration (coarse phonetic proxy).
    en_lat = " ".join(en_tokens)
    ur_tokens_latin = [urdu_to_latin(t) for t in ur_tokens]
    ur_lat = " ".join(ur_tokens_latin)
    fuzzy_score = fuzz.token_sort_ratio(en_lat, ur_lat) / 100.0 if (en_lat and ur_lat) else 0.0

    # Overlap: how many English content tokens are covered by the Urdu stem
    # either directly (loan words / cognates) or via the bilingual keyword map.
    ur_text = strip_diacritics(normalise(ur_stem))
    matched = 0
    for et in en_tokens:
        if et in ur_text:
            matched += 1
        else:
            ur_equivs = _BILINGUAL_KW.get(et, set())
            if any(kw in ur_text for kw in ur_equivs):
                matched += 1
    overlap_score = matched / len(en_tokens) if en_tokens else 0.0

    # Length ratio penalises large omissions/additions in the stem.
    en_len = len(normalise(en_stem))
    ur_len = len(normalise(ur_stem))
    length_ratio = min(en_len, ur_len) / max(en_len, ur_len) if max(en_len, ur_len) else 0.0

    # Weighted aggregate. Overlap is the strongest cross-lingual signal here
    # because the bilingual map captures domain terms; fuzzy is only a weak
    # phonetic fallback.
    similarity = 0.15 * fuzzy_score + 0.60 * overlap_score + 0.25 * length_ratio

    # Confidence grows with token coverage.
    token_count = len(en_tokens) + len(ur_tokens)
    confidence = min(0.95, 0.4 + 0.05 * token_count)

    return {
        "similarity": round(similarity, 3),
        "confidence": round(confidence, 3),
        "fuzzy_score": round(fuzzy_score, 3),
        "overlap_score": round(overlap_score, 3),
        "length_ratio": round(length_ratio, 3),
    }


def semantic_flag(en: str, ur: str, threshold: float = 0.45) -> Dict[str, object]:
    """Return a flag dict if semantic similarity suggests drift."""
    scores = semantic_similarity(en, ur)
    if scores["similarity"] < threshold and scores["confidence"] >= 0.5:
        return {
            "raised": True,
            "category": "Semantic drift",
            "severity": "medium",
            "message": (
                f"Cross-lingual semantic similarity is low ({scores['similarity']:.2f}); "
                "the questions may ask conceptually different things."
            ),
            "en_evidence": en[:200],
            "ur_evidence": ur[:200],
            "confidence": scores["confidence"],
            "scores": scores,
        }
    return {"raised": False, "scores": scores}
