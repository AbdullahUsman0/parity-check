"""Evaluation metrics for ParityLens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from paritylens.engine.pipeline import PairResult, run_pipeline


CATEGORY_MAP = {
    "numeric": "Numeric mismatch",
    "unit": "Unit mismatch",
    "negation": "Negation/polarity mismatch",
    "option": "Answer-option mismatch or reordering",
    "formula": "Formula/symbol mismatch",
    "entity": "Named-entity mismatch",
    "condition": "Missing condition or constraint",
    "semantic": "Semantic drift",
    "none": None,
}


@dataclass
class Metrics:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def fp_per_100(self, total: int) -> float:
        return self.fp / total * 100 if total else 0.0


def evaluate_results(results: List[PairResult]) -> Dict:
    categories = {v for v in CATEGORY_MAP.values() if v}
    per_cat = {cat: Metrics(0, 0, 0, 0) for cat in categories}
    overall = Metrics(0, 0, 0, 0)
    latency_ms = []

    for r in results:
        true_label = r.id  # not used; true category is inferred via a side channel below.
        latency_ms.append(r.elapsed_ms)

    # Caller is expected to pair results with ground-truth rows; this function accepts
    # results that already carry a synthetic `true_mismatch` field attached as metadata.
    return {
        "per_category": per_cat,
        "overall": overall,
        "latency_ms": 0.0,
        "fp_per_100": 0.0,
    }


def evaluate_with_ground_truth(
    results: List[PairResult],
    true_mismatches: List[str],
) -> Dict:
    categories = {v for v in CATEGORY_MAP.values() if v}
    per_cat = {cat: Metrics(0, 0, 0, 0) for cat in categories}
    overall = Metrics(0, 0, 0, 0)
    latency_ms = []

    for r, true in zip(results, true_mismatches):
        latency_ms.append(r.elapsed_ms)
        true_cat = CATEGORY_MAP.get(true)
        raised_cats = {f["category"] for f in r.all_flags}

        # Overall: positive if any flag raised; negative otherwise.
        if true_cat is None:
            if raised_cats:
                overall.fp += len(raised_cats)
            else:
                overall.tn += 1
        else:
            if true_cat in raised_cats:
                overall.tp += 1
            else:
                overall.fn += 1
            # Extra flags beyond the true category count as FP.
            overall.fp += len(raised_cats - {true_cat})

        # Per-category.
        for cat in categories:
            m = per_cat[cat]
            is_true = cat == true_cat
            is_raised = cat in raised_cats
            if is_true and is_raised:
                m.tp += 1
            elif is_true and not is_raised:
                m.fn += 1
            elif not is_true and is_raised:
                m.fp += 1
            else:
                m.tn += 1

    total = len(results)
    avg_latency = sum(latency_ms) / total if total else 0.0

    return {
        "per_category": {
            cat: {
                "tp": m.tp,
                "fp": m.fp,
                "fn": m.fn,
                "tn": m.tn,
                "precision": round(m.precision, 3),
                "recall": round(m.recall, 3),
                "f1": round(m.f1, 3),
            }
            for cat, m in per_cat.items()
        },
        "overall": {
            "tp": overall.tp,
            "fp": overall.fp,
            "fn": overall.fn,
            "tn": overall.tn,
            "precision": round(overall.precision, 3),
            "recall": round(overall.recall, 3),
            "f1": round(overall.f1, 3),
        },
        "latency_ms": round(avg_latency, 2),
        "fp_per_100": round(overall.fp / total * 100, 2) if total else 0.0,
        "total_questions": total,
    }


def compare_configs(df, semantic_threshold: float = 0.45) -> Dict[str, Dict]:
    comparison = {}
    for config in ("rules", "semantic", "hybrid"):
        results = run_pipeline(df, config=config, semantic_threshold=semantic_threshold)
        comparison[config] = evaluate_with_ground_truth(
            results, df["true_mismatch"].tolist()
        )
    return comparison
