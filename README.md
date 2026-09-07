# ParityLens

A prototype bilingual exam-parity auditor for Urdu–English question papers.

## What it does

- Upload a CSV of paired English/Urdu exam questions.
- Runs deterministic checks (numbers, units, negation, answer options, formulas, named entities).
- Adds a lightweight cross-lingual semantic similarity score to catch conceptual drift.
- Presents a reviewer queue in Streamlit.
- Exports a QA report PDF with accepted/rejected flags.

## Run locally

```bash
cd paritylens
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL printed in the terminal and either upload your own CSV or click **Load 20-question demo paper**.

## CSV format

| Column | Description |
|--------|-------------|
| `id` | Question identifier |
| `question_number` | Display number |
| `english` | English question text (stem + options) |
| `urdu` | Urdu question text (stem + options) |
| `true_mismatch` (optional) | `1` if the pair is known to be defective, `0` otherwise |

## Deploy

The easiest public deployment is **Streamlit Community Cloud**:

1. Go to <https://share.streamlit.io/> and sign in with GitHub.
2. Create a new app, select this repository, and set the main file path to `paritylens/app.py`.
3. Deploy.

The app will stay in sync with the repo on every push to `master`.

## Project structure

```
paritylens/
├── app.py                 # Streamlit UI
├── requirements.txt       # Python dependencies
├── engine/
│   ├── rules.py           # Deterministic parity rules
│   ├── semantic.py        # Cross-lingual similarity scorer
│   └── pipeline.py        # Orchestrates checks into results
├── eval/
│   └── evaluate.py        # Benchmark metrics & config comparison
└── data/
    ├── demo_paper.csv     # 20-question demo with 5 seeded defects
    ├── benchmark.csv      # 30-question labelled benchmark
    └── generate_datasets.py
```

## Notes

- PDF/image OCR is stubbed in this prototype; inputs are expected as CSV.
- The semantic scorer is intentionally lightweight (keyword overlap + fuzzy fallback) so the demo runs without GPU or external API calls.
