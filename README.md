
# AI-assisted Unit Test Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📖 Project Overview

**AI-assisted Unit Test Generation** is an intelligent system designed to help software developers automatically generate high-quality unit tests for their code. Writing unit tests is often time-consuming and repetitive, but this project leverages advanced AI models to generate tests quickly and efficiently. 

The system also provides detailed metrics, hallucination detection, and performance analysis to ensure that the generated tests are accurate, useful, and maintainable. It supports multiple AI models and integrates visualization tools to make test evaluation easier.

---

## 🧾 Abstract-style Summary

This project implements a complete, reproducible prototype for AI-assisted unit test generation, wrapped as a FastAPI service and supported by an automated evaluation pipeline. Given Python source code, the system generates candidate pytest tests, validates them with syntax checks, static safety rules, and optional sandboxed execution, and then exposes the results via JSON APIs and command-line tools. Evaluation modules compute BLEU and embedding-based similarity between reference and generated tests, run coverage analysis, and quantify hallucination rates, enabling empirical study of model behavior.

Beyond raw generation, the system emphasizes safety and accountability. The API explicitly flags meaningless assertions (such as plain `assert True`) as potential hallucinations, records possible hallucinations during dataset evaluation, and logs all API calls, governance decisions, and evaluation runs to structured JSONL logs. A simple generator–validator workflow provides an ethically governed multi-agent setup that can be discussed in a research report as a lightweight, transparent approach to governing AI-assisted software engineering tools.

---

## ✨ Key Features

- **AI-Powered Test Generation**: Automatically generates unit tests for your code.
- **Hallucination Detection**: Detects potential inaccuracies or irrelevant outputs in generated tests.
- **Comprehensive Metrics**: Tracks quality using BLEU, ROUGE, hallucination rates, code coverage, and test effectiveness.
- **Interactive Dashboard**: Visualizes test generation results and model performance.
- **Multi-Model Support**: Works with multiple LLM providers (OpenAI, Anthropic, etc.) for flexibility.

---

## 🚀 Installation

1. **Clone the repository**:

git clone https://github.com/yehiahesham2938/AI-assisted-Unit-Test-Generation.git
cd AI-assisted-Unit-Test-Generation


2. **Create a virtual environment**:


python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate


3. **Install dependencies**:


pip install -r requirements.txt


---

## 🛠️ Usage

### Run the FastAPI Service (Phase 3)

1. Activate your virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the API server (from the project root):

   ```bash
   uvicorn app:app --reload
   ```

3. Open the interactive API docs in your browser:

   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

#### Endpoint: `/generate-tests` (POST)

Generate unit tests for a single Python function/module supplied as a string.

Example JSON body:

```json
{
  "source_code": "def add(a, b):\n    return a + b\n",
  "provider": "hf",
  "temperature": 0.0,
  "max_tokens": 256
}
```

Example `curl` request:

```bash
curl -X POST "http://127.0.0.1:8000/generate-tests" \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "def add(a, b):\\n    return a + b\\n",
    "provider": "hf",
    "temperature": 0.0,
    "max_tokens": 256
  }'
```

The response includes:

- `tests`: generated pytest file contents as a string
- `prompt`: the underlying LLM prompt used
- `metadata`: provider/model info, latency, and basic syntax validation flags

#### Endpoint: `/generate-tests-validated` (POST)

This endpoint wraps test generation in a simple **generator–validator workflow**:

- Generator: calls the same LLM-based engine as `/generate-tests`.
- Validator: runs syntax checks, rule-based safety checks, and optional pytest in a sandbox.

Example JSON body:

```json
{
  "source_code": "def add(a, b):\n    return a + b\n",
  "provider": "hf",
  "temperature": 0.0,
  "max_tokens": 256,
  "run_pytest": true
}
```

The response includes:

- `tests`: generated pytest file contents as a string
- `prompt`: the prompt given to the generator
- `generator_metadata`: provider/model info and latency
- `governance`: structured validation report with:
  - `safe`: overall safety flag (syntax + simple static checks)
  - `syntax_ok` / `syntax_error`: Python compilation result
  - `reasons`: reasons if marked unsafe
  - `warnings`: non-fatal issues (e.g. no asserts, pytest not run)
  - `pytest_passed`: whether sandboxed pytest succeeded when `run_pytest=true`

##### Demonstrating the ethically governed multi-agent workflow (Bonus)

The `/generate-tests-validated` endpoint is the main interface for the **ethically governed multi-agent workflow** required for the Phase 3 bonus. Internally, it delegates to `multi_agent_workflow.py`, where a generator agent produces candidate tests and a validator agent enforces governance controls:

- **Safety**: static rules flag potentially dangerous patterns (filesystem, subprocess, network access) and meaningless assertions such as plain `assert True`.
- **Transparency & explainability**: the `governance` object in the response explains why a set of tests is considered safe or unsafe via `reasons`, `warnings`, and `syntax_error`.
- **Accountability**: every multi-agent run is logged to `logs/multi_agent_workflow.jsonl` with the source length, test length, generator metadata, and governance report.

To demonstrate this workflow in experiments or in your report:

1. Start the API server:

   ```bash
   uvicorn app:app --reload --host 127.0.0.1 --port 8001
   ```

2. Open Swagger UI at `http://127.0.0.1:8001/docs` and locate `POST /generate-tests-validated`.
3. Click **Try it out**, keep the example JSON body (which uses the lightweight `mock` provider), and click **Execute**.
4. Inspect the `governance` field in the response to see the validator's decision, including any hallucination flags or safety reasons.
5. Optionally, open `logs/multi_agent_workflow.jsonl` to see the same governance information recorded for transparency and later analysis.

#### Endpoint: `/evaluate-dataset` (POST)

Run automated evaluation over the on-disk dataset (`data/functions`, `data/expected_tests`, `data/generated_tests`).

Example JSON body:

```json
{
  "functions_dir": "data/functions",
  "expected_tests_dir": "data/expected_tests",
  "generated_tests_dir": "data/generated_tests",
  "regenerate": false,
  "run_pytest": true,
  "run_coverage": false,
  "max_pairs": 50
}
```

The response includes:

- Per-file BLEU and embedding cosine similarity
- A `possible_hallucination` flag based on low similarity
- Aggregated summary statistics
- Optional pytest and coverage results

### CLI Utilities (Existing)

You can still use the original scripts directly from the command line.

#### Generate Unit Tests for the Dataset

```bash
python generate_tests.py
```

#### Analyze Hallucinations

```bash
python -m analysis.hallucination_analysis.analyze_hallucination_metrics
```

#### Generate Coverage Report for Generated Tests

```bash
python -m eval.evaluate_coverage
```




## ✅ Phase 3 Requirements: Implementation Summary

This section summarizes how the system satisfies the Phase 3 requirements for a complete, runnable AI-enabled software engineering prototype.

- **Complete running prototype (end-to-end)**  
  The project runs end-to-end, from AI test generation to automated evaluation and analysis. The core generation logic lives in `generate_tests.py`, which is reused by the FastAPI service (`app.py`) and by the evaluation scripts under `eval/`. The system can be executed locally with a single environment (`requirements.txt`) and configuration file (`config.yaml`).

- **AI functionality fully integrated**  
  The primary AI functionality is **unit test generation**. The function `generate_tests_for_source` in `generate_tests.py` takes Python source code as input and produces candidate pytest tests. This function is consumed by:
  - The **FastAPI endpoints** `/generate-tests` and `/generate-tests-validated` in `app.py`.
  - The CLI script `generate_tests.py` for dataset-wide generation.  
  Evaluation utilities in `eval/` and hallucination analysis code in `analysis/hallucination_analysis/` are tightly integrated with the generated tests, providing a coherent AI-assisted testing workflow.

- **FastAPI service with documented JSON input/output**  
  The API wrapper is implemented in `app.py` using FastAPI. It exposes:
  - `GET /` and `GET /health` for service status.
  - `POST /generate-tests` for basic AI test generation.
  - `POST /generate-tests-validated` for the governed multi-agent workflow.
  - `POST /evaluate-dataset` for automated evaluation over on-disk datasets.  
  Request and response bodies are defined via Pydantic models (`GenerateTestsRequest`, `GenerateTestsResponse`, `GenerateTestsValidatedRequest`, `GenerateTestsValidatedResponse`, `EvaluateDatasetRequest`, `EvaluateDatasetResponse`). Each request model includes a JSON example (`schema_extra`) so the interactive docs at `/docs` provide **concrete, executable examples** of valid input and output.

- **Reproducible execution (local)**  
  All dependencies are specified in `requirements.txt`. Configuration for models, decoding parameters, and dataset paths is centralized in `config.yaml`. The main workflows can be reproduced locally via:
  - `python generate_tests.py` (dataset-wide generation).
  - `python -m eval.evaluate_results` (pytest-based evaluation).
  - `python -m eval.evaluate_coverage` (coverage-based evaluation).
  - `python -m analysis.hallucination_analysis.analyze_hallucination_metrics` (hallucination analysis and report).  
  The same logic is then exposed via FastAPI, ensuring that API behavior matches the CLI pipelines.

- **Minimal safety guardrails**  
  The system implements multiple lightweight safety and quality checks:
  - **Input validation**: FastAPI endpoints reject empty `source_code` with clear 400 errors.
  - **Syntax validation**: Generated tests are compiled with `compile()`; syntax errors are surfaced in the API metadata and in the multi-agent governance report.
  - **Static safety checks**: The validator in `multi_agent_workflow.py` (`_static_safety_checks`) flags potentially unsafe patterns (e.g., `import os`, `subprocess`, filesystem and network access) and warns if no assertions are present.
  - **Meaningless assertion detection**: Both the single-agent and multi-agent flows explicitly detect `assert True` as a **meaningless assertion**. In `/generate-tests`, the response `metadata` includes `status="failed"`, `reason="Meaningless assertion detected"`, and `hallucination=true` when this pattern appears. In the multi-agent workflow, the governance report sets `hallucination=true` and records a corresponding reason.
  - **Sandboxed execution**: The multi-agent validator runs pytest in a temporary directory (`_run_pytest_in_temp`) to avoid polluting the main environment.
  - **Resource safety**: `eval/metrics_utils.py` lazily loads `sentence_transformers` and degrades gracefully if the embedding model cannot be loaded, preventing TensorFlow-related crashes in the API.

- **Clear README with setup, run instructions, and example requests**  
  This `README.md` provides end-to-end instructions: cloning the repo, creating a virtual environment, installing dependencies, running the FastAPI server, and exercising all endpoints. It also documents CLI utilities for generation, coverage, and hallucination analysis. Example JSON bodies are given for all major endpoints, and Swagger UI at `/docs` exposes the same information interactively.

- **AI service wrapper (FastAPI endpoint)**  
  The FastAPI application in `app.py` acts as the AI service wrapper. It encapsulates configuration loading, logging, error handling, and calls into the core generator and evaluation modules. The service can be used programmatically (via HTTP clients) or interactively via the automatically generated OpenAPI documentation.

- **Automated evaluation module**  
  Automated evaluation is implemented in the `eval/` package and integrated into the `/evaluate-dataset` endpoint:
  - `eval.evaluate_results.run_pytest_on_generated_tests` executes generated tests with pytest and reports return codes and output.
  - `eval.evaluate_coverage.run_coverage` computes coverage for target functions when executed by generated tests, producing an HTML report.
  - `eval.metrics_utils` defines BLEU and embedding cosine similarity metrics, which are used in `_compute_pair_metrics` in `app.py` to score (expected, generated) test pairs.  
  The evaluation response includes per-file scores, a `possible_hallucination` flag, and aggregate statistics such as average BLEU, average cosine similarity, and hallucination rate.

- **Explicit handling of incorrect or hallucinated outputs**  
  The system treats low-quality or incorrect outputs as first-class objects:
  - In `/generate-tests`, the response metadata records `syntactic_ok`, `syntax_error`, and hallucination-related fields. Meaningless assertions (`assert True`) cause the status to be marked as failed with an explicit reason.
  - In `/generate-tests-validated`, the `governance` object contains `safe`, `syntax_ok`, `syntax_error`, `reasons`, `warnings`, `pytest_passed`, and `hallucination`, providing a structured explanation of validation and safety decisions.
  - In dataset evaluation, `PairMetrics.possible_hallucination` and `EvaluationSummary.hallucination_rate` quantify hallucination at the dataset level.
  - The hallucination analysis script under `analysis/hallucination_analysis/` produces an HTML report and plots for deeper inspection.

- **Logging of model outputs and failures**  
  All major operations write structured logs:
  - `logs/api_calls.jsonl` records FastAPI requests, responses, and exceptions.
  - `logs/eval_runs.jsonl` records dataset evaluation runs and results.
  - `logs/multi_agent_workflow.jsonl` records each multi-agent generation, including governance decisions and relevant metadata.  
  These logs support transparency, debugging, and empirical analysis for the accompanying research report.

- **Optional: ethically governed multi-agent workflow**  
  The optional bonus requirement is addressed via `multi_agent_workflow.py` and the `/generate-tests-validated` endpoint. The system implements a simple generator–validator architecture:
  - The **generator** delegates to the existing test generation function.
  - The **validator** performs syntax checks, static safety analysis, optional sandboxed pytest, and hallucination detection.  
  The resulting `governance` report is returned to the caller and logged, providing **safety, transparency, and accountability** without relying on heavyweight orchestration frameworks. This design can be discussed in the research paper as an example of an ethically governed AI workflow tailored to the project’s resource constraints.


## 📁 Project Structure

AI-assisted-Unit-Test-Generation/
├── ai_testgen/              
│   ├── generators/          # Test generation modules
│   ├── models/              # AI model integrations
│   └── utils/               # Helper functions
│
├── analysis/                
│   ├── Hallucination&Plots/ # Metrics & visualizations
│   ├── analyze_hallucination_metrics.py
│   └── generate_dashboard.py
│
├── tests/                   # Example test files
├── examples/                # Sample usage scripts
├── docs/                    # Documentation
├── requirements.txt         # Dependencies
└── README.md                # Project overview




## 📊 Metrics & Analysis

The project includes robust evaluation tools:

* **Hallucination Rate**: Percentage of generated tests that contain inaccuracies.
* **Code Coverage**: Measures how well the generated tests cover the original code.
* **Test Effectiveness**: Evaluates the quality and reliability of generated tests.
* **Model Comparison**: Compare the performance of different AI models in test generation.

### Viewing Metrics


python -m analysis.analyze_hallucination_metrics


Open the generated `hallucination_analysis.html` in a browser to explore the interactive dashboard.


## ⚠️ Limitations and Future Work

While the current prototype satisfies the Phase 3 requirements and runs end-to-end, it deliberately trades off some realism for robustness and ease of reproduction on modest hardware. The default generator uses a lightweight mock provider rather than large proprietary models, and the static safety checks focus on simple string-based heuristics (e.g., detecting dangerous imports or meaningless `assert True` statements) instead of deep program analysis. Evaluation is performed on a relatively small, curated dataset, and the metrics capture surface-level similarity and coverage rather than full semantic correctness of tests.

Future work includes integrating stronger, resource-aware model backends (e.g., configurable OpenAI or Hugging Face models with clear API key management), expanding the benchmark dataset to more realistic and diverse codebases, and enriching the governance layer. In particular, the current generator–validator workflow could be extended with richer policies (fairness, robustness, model comparison), more interpretable validation signals, and tighter integration with orchestration frameworks such as CrewAI or LangGraph. Containerization and CI integration would further improve reproducibility and make it easier to evaluate the system across different environments and parameter settings.


## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create a new branch:


git checkout -b feature/your-feature


3. Commit your changes:


git commit -m "Add new feature"


4. Push to the branch:


git push origin feature/your-feature


5. Open a Pull Request



## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.



## 📧 Contact

For questions or feedback, please open an issue or contact the maintainers.



