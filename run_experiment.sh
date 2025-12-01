#!/usr/bin/env bash
set -e
python generate_tests.py
python eval/evaluate_results.py
python eval/evaluate_coverage.py
python - <<'PY'
from eval.metrics_utils import embedding_cosine, bleu_score
# iterate generated tests and expected tests to compute metrics...
print("Postprocessing metrics (implement per dataset)")
PY
