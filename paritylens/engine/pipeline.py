"""End-to-end parity pipeline orchestrator."""

from __future__ import annotations

import dataclasses
import time
from typing import Dict, List, Optional

import pandas as pd

from .rules import Flag, run_deterministic_checks
from .semantic import semantic_flag, semantic_similarity


@dataclasses.dataclass
class PairResult:
    id: str
    question_number: int
    english: str
    urdu: str
    deterministic_flags: List[Flag]
    semantic_result: Dict
    elapsed_ms: float
    config: str  # 'rules', 'semantic', or 'hybrid'

    @property
    def all_flags(self) -> List[Dict]:
        flags = []
        for f in self.deterministic_flags:
            flags.append(
                {
                    "category": f.category,
                    "severity": f.severity,
                    "message": f.message,
                    "en_evidence": f.en_evidence,
                    "ur_evidence": f.ur_evidence,
                    "confidence": f.confidence,
                    "source": "rules",
                }
            )
        if self.semantic_result.get("raised"):
            flags.append(
                {
                    "category": self.semantic_result["category"],
                    "severity": self.semantic_result["severity"],
                    "message": self.semantic_result["message"],
                    "en_evidence": self.semantic_result["en_evidence"],
                    "ur_evidence": self.semantic_result["ur_evidence"],
                    "confidence": self.semantic_result["confidence"],
                    "source": "semantic",
                    "scores": self.semantic_result.get("scores", {}),
                }
            )
        return flags

    @property
    def is_flagged(self) -> bool:
        return len(self.all_flags) > 0

    @property
    def risk_score(self) -> float:
        if not self.all_flags:
            return 0.0
        weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        return round(
            sum(weights.get(f["severity"], 0.5) * f["confidence"] for f in self.all_flags)
            / len(self.all_flags),
            3,
        )


def run_on_row(
    row: Dict,
    config: str = "hybrid",
    semantic_threshold: float = 0.45,
) -> PairResult:
    en = str(row.get("english", ""))
    ur = str(row.get("urdu", ""))
    qid = str(row.get("id", ""))
    qnum = int(row.get("question_number", 0))

    start = time.perf_counter()

    det_flags: List[Flag] = []
    if config in ("rules", "hybrid"):
        det_flags = run_deterministic_checks(en, ur)

    sem_result = {"raised": False, "scores": semantic_similarity(en, ur)}
    if config in ("semantic", "hybrid"):
        sem_result = semantic_flag(en, ur, threshold=semantic_threshold)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return PairResult(
        id=qid,
        question_number=qnum,
        english=en,
        urdu=ur,
        deterministic_flags=det_flags,
        semantic_result=sem_result,
        elapsed_ms=round(elapsed_ms, 2),
        config=config,
    )


def run_pipeline(
    df: pd.DataFrame,
    config: str = "hybrid",
    semantic_threshold: float = 0.45,
) -> List[PairResult]:
    results = []
    for _, row in df.iterrows():
        results.append(run_on_row(row.to_dict(), config=config, semantic_threshold=semantic_threshold))
    return results


def load_paper_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)
