from pathlib import Path
import os
import datetime
import traceback
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

from generate_tests import (
    load_config,
    generate_tests_for_source,
    log_jsonl,
    main as generate_dataset_tests_main,
)
from multi_agent_workflow import generate_tests_validated as ma_generate_tests_validated
from eval.evaluate_results import run_pytest_on_generated_tests
from eval.metrics_utils import embedding_cosine, bleu_score
from eval.evaluate_coverage import run_coverage


app = FastAPI(
    title="AI-assisted Unit Test Generation Service (v2)",
    description="FastAPI service for AI-based unit test generation and automated evaluation.",
    version="0.1.0",
)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "note": "FastAPI service is running, but this specific path does not exist.",
                "requested_path": request.url.path,
                "available_endpoints": [
                    "/health",
                    "/generate-tests",
                    "/generate-tests-validated",
                    "/evaluate-dataset",
                    "/docs",
                    "/redoc",
                ],
            },
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "AI-assisted Unit Test Generation FastAPI service is running.",
        "endpoints": [
            "/generate-tests",
            "/generate-tests-validated",
            "/evaluate-dataset",
            "/docs",
            "/redoc",
        ],
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


class GenerateTestsRequest(BaseModel):
    source_code: str = Field(
        ..., description="Python source code to generate unit tests for.", max_length=20000
    )
    provider: Optional[str] = Field(
        None, description="Override model.provider ('openai' or 'hf')."
    )
    openai_model: Optional[str] = Field(
        None, description="Override OpenAI chat model name."
    )
    hf_model: Optional[str] = Field(
        None, description="Override Hugging Face model name."
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Override decoding.temperature."
    )
    max_tokens: Optional[int] = Field(
        None, ge=16, le=2048, description="Override decoding.max_tokens (capped)."
    )

    class Config:
        schema_extra = {
            "example": {
                "source_code": "def add(a, b):\n    return a + b",
                "provider": "mock",
                "openai_model": None,
                "hf_model": None,
                "temperature": 0.2,
                "max_tokens": 256,
            }
        }


class GenerateTestsResponse(BaseModel):
    tests: str
    prompt: str
    metadata: Dict[str, Any]


class GovernanceReport(BaseModel):
    safe: bool
    syntax_ok: bool
    syntax_error: Optional[str]
    reasons: List[str]
    warnings: List[str]
    pytest_passed: Optional[bool]
    hallucination: Optional[bool]


class GenerateTestsValidatedRequest(GenerateTestsRequest):
    run_pytest: bool = Field(
        True,
        description="Run pytest in a temporary sandbox as part of validation.",
    )

    class Config:
        schema_extra = {
            "example": {
                "source_code": "def add(a, b):\n    return a + b",
                "provider": "mock",
                "openai_model": None,
                "hf_model": None,
                "temperature": 0.2,
                "max_tokens": 256,
                "run_pytest": True,
            }
        }


class GenerateTestsValidatedResponse(BaseModel):
    tests: str
    prompt: str
    generator_metadata: Dict[str, Any]
    governance: GovernanceReport


class EvaluateDatasetRequest(BaseModel):
    functions_dir: str = Field("data/functions", description="Directory with Python source functions.")
    expected_tests_dir: str = Field(
        "data/expected_tests", description="Directory with reference unit tests."
    )
    generated_tests_dir: str = Field(
        "data/generated_tests", description="Directory with generated unit tests."
    )
    regenerate: bool = Field(
        False,
        description="If true, regenerate tests for functions_dir using config.yaml before evaluation.",
    )
    run_pytest: bool = Field(True, description="Run pytest on generated tests.")
    run_coverage: bool = Field(
        False,
        description="Run coverage on generated tests. Coverage HTML will be written under analysis/coverage_html.",
    )
    max_pairs: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum number of (expected, generated) test file pairs to score.",
    )

    class Config:
        schema_extra = {
            "example": {
                "functions_dir": "data/functions",
                "expected_tests_dir": "data/expected_tests",
                "generated_tests_dir": "data/generated_tests",
                "regenerate": False,
                "run_pytest": True,
                "run_coverage": False,
                "max_pairs": 50,
            }
        }


class PairMetrics(BaseModel):
    file: str
    status: str
    bleu: Optional[float] = None
    embedding_cosine: Optional[float] = None
    possible_hallucination: Optional[bool] = None


class EvaluationSummary(BaseModel):
    num_pairs: int
    avg_bleu: Optional[float]
    avg_embedding_cosine: Optional[float]
    hallucination_rate: Optional[float]


class EvaluateDatasetResponse(BaseModel):
    summary: EvaluationSummary
    pairs: List[PairMetrics]
    pytest_returncode: Optional[int]
    pytest_output: Optional[str]
    coverage_report_path: Optional[str]


def _safe_log(entry: Dict[str, Any], jsonl_path: Path) -> None:
    try:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        log_jsonl(entry, str(jsonl_path))
    except Exception:
        pass


def _compute_pair_metrics(
    expected_tests_dir: str, generated_tests_dir: str, max_pairs: int
) -> (List[Dict[str, Any]], Dict[str, Any]):
    expected_path = Path(expected_tests_dir)
    generated_path = Path(generated_tests_dir)

    if not expected_path.exists() or not expected_path.is_dir():
        raise HTTPException(status_code=400, detail="expected_tests_dir does not exist or is not a directory.")
    if not generated_path.exists() or not generated_path.is_dir():
        raise HTTPException(status_code=400, detail="generated_tests_dir does not exist or is not a directory.")

    pairs: List[Dict[str, Any]] = []
    bleu_values: List[float] = []
    cosine_values: List[float] = []
    halluc_flags: List[bool] = []

    for expected_file in sorted(expected_path.glob("*.py"))[:max_pairs]:
        name = expected_file.name
        expected_text = expected_file.read_text(encoding="utf-8")
        gen_file = generated_path / name

        if not gen_file.exists():
            item = {
                "file": name,
                "status": "missing_generated",
                "bleu": None,
                "embedding_cosine": None,
                "possible_hallucination": True,
            }
            pairs.append(item)
            halluc_flags.append(True)
            continue

        generated_text = gen_file.read_text(encoding="utf-8")

        try:
            bleu = bleu_score(expected_text, generated_text)
        except Exception:
            bleu = None

        try:
            cos = embedding_cosine(expected_text, generated_text)
        except Exception:
            cos = None

        possible_hallucination = False
        if bleu is not None or cos is not None:
            if bleu is not None and bleu < 0.2:
                possible_hallucination = True
            if cos is not None and cos < 0.5:
                possible_hallucination = True

        pairs.append(
            {
                "file": name,
                "status": "ok",
                "bleu": bleu,
                "embedding_cosine": cos,
                "possible_hallucination": possible_hallucination,
            }
        )

        if bleu is not None:
            bleu_values.append(float(bleu))
        if cos is not None:
            cosine_values.append(float(cos))
        halluc_flags.append(possible_hallucination)

    summary = {
        "num_pairs": len(pairs),
        "avg_bleu": float(sum(bleu_values) / len(bleu_values)) if bleu_values else None,
        "avg_embedding_cosine": float(sum(cosine_values) / len(cosine_values)) if cosine_values else None,
        "hallucination_rate": float(sum(1 for f in halluc_flags if f) / len(halluc_flags)) if halluc_flags else None,
    }

    return pairs, summary


@app.post("/generate-tests", response_model=GenerateTestsResponse)
def generate_tests_endpoint(request: GenerateTestsRequest) -> GenerateTestsResponse:
    if not request.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code must not be empty.")

    cfg = load_config("config.yaml")

    if request.provider in {"openai", "hf"}:
        cfg["model"]["provider"] = request.provider

    if request.openai_model:
        cfg["model"]["openai_model"] = request.openai_model

    if request.hf_model:
        cfg["model"]["hf_model"] = request.hf_model

    if request.temperature is not None:
        cfg.setdefault("decoding", {})
        cfg["decoding"]["temperature"] = float(request.temperature)

    if request.max_tokens is not None:
        cfg.setdefault("decoding", {})
        cfg["decoding"]["max_tokens"] = int(min(request.max_tokens, 2048))

    provider = cfg["model"]["provider"]
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY environment variable is not set but provider 'openai' was requested.",
        )

    api_log_path = Path("logs") / "api_calls.jsonl"

    try:
        tests, prompt, metadata = generate_tests_for_source(request.source_code, cfg)

        syntactic_ok = True
        syntax_error = None
        try:
            compile(tests, "<generated_tests>", "exec")
        except SyntaxError as e:
            syntactic_ok = False
            syntax_error = str(e)

        response_metadata: Dict[str, Any] = dict(metadata)
        response_metadata["syntactic_ok"] = syntactic_ok
        response_metadata["syntax_error"] = syntax_error

        # Simple hallucination / quality check: detect meaningless assertions
        meaningless_assertion = "assert True" in tests
        if meaningless_assertion:
            # Equivalent to the user's snippet:
            # if "assert True" in generated_tests:
            #     return {"status": "failed", "reason": "Meaningless assertion detected", "hallucination": True}
            response_metadata["status"] = "failed"
            response_metadata["reason"] = "Meaningless assertion detected"
            response_metadata["hallucination"] = True
        else:
            response_metadata.setdefault("status", "ok")
            response_metadata.setdefault("hallucination", False)

        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "generate-tests",
            "provider": provider,
            "request": {
                "source_len": len(request.source_code),
                "temperature": cfg.get("decoding", {}).get("temperature"),
                "max_tokens": cfg.get("decoding", {}).get("max_tokens"),
            },
            "response": {
                "tests_len": len(tests),
                "syntactic_ok": syntactic_ok,
                "hallucination": bool(response_metadata.get("hallucination")),
            },
        }
        _safe_log(log_entry, api_log_path)

        return GenerateTestsResponse(tests=tests, prompt=prompt, metadata=response_metadata)

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "generate-tests",
            "error": str(e),
            "traceback": tb,
        }
        _safe_log(log_entry, api_log_path)
        raise HTTPException(status_code=500, detail="Internal error while generating tests.")


@app.post("/evaluate-dataset", response_model=EvaluateDatasetResponse)
def evaluate_dataset_endpoint(request: EvaluateDatasetRequest) -> EvaluateDatasetResponse:
    functions_dir = request.functions_dir
    expected_tests_dir = request.expected_tests_dir
    generated_tests_dir = request.generated_tests_dir

    if not Path(functions_dir).exists():
        raise HTTPException(status_code=400, detail="functions_dir does not exist.")

    eval_log_path = Path("logs") / "eval_runs.jsonl"

    pytest_returncode: Optional[int] = None
    pytest_output: Optional[str] = None
    coverage_report_path: Optional[str] = None

    try:
        if request.regenerate:
            generate_dataset_tests_main("config.yaml")

        pairs_raw, summary_raw = _compute_pair_metrics(
            expected_tests_dir=expected_tests_dir,
            generated_tests_dir=generated_tests_dir,
            max_pairs=request.max_pairs,
        )

        if request.run_pytest:
            rc, out = run_pytest_on_generated_tests(
                generated_dir=generated_tests_dir, functions_dir=functions_dir
            )
            pytest_returncode = rc
            pytest_output = (out or "")[:4000]

        if request.run_coverage:
            run_coverage(functions_dir=functions_dir, tests_dir=generated_tests_dir)
            coverage_report_path = "analysis/coverage_html/index.html"

        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "evaluate-dataset",
            "request": request.dict(),
            "summary": summary_raw,
            "pytest_returncode": pytest_returncode,
        }
        _safe_log(log_entry, eval_log_path)

        pairs_models = [PairMetrics(**p) for p in pairs_raw]
        summary_model = EvaluationSummary(**summary_raw)

        return EvaluateDatasetResponse(
            summary=summary_model,
            pairs=pairs_models,
            pytest_returncode=pytest_returncode,
            pytest_output=pytest_output,
            coverage_report_path=coverage_report_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "evaluate-dataset",
            "error": str(e),
            "traceback": tb,
        }
        _safe_log(log_entry, eval_log_path)
        raise HTTPException(status_code=500, detail="Internal error while evaluating dataset.")


@app.post("/generate-tests-validated", response_model=GenerateTestsValidatedResponse)
def generate_tests_validated_endpoint(
    request: GenerateTestsValidatedRequest,
) -> GenerateTestsValidatedResponse:
    if not request.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code must not be empty.")

    cfg = load_config("config.yaml")

    if request.provider in {"openai", "hf"}:
        cfg["model"]["provider"] = request.provider

    if request.openai_model:
        cfg["model"]["openai_model"] = request.openai_model

    if request.hf_model:
        cfg["model"]["hf_model"] = request.hf_model

    if request.temperature is not None:
        cfg.setdefault("decoding", {})
        cfg["decoding"]["temperature"] = float(request.temperature)

    if request.max_tokens is not None:
        cfg.setdefault("decoding", {})
        cfg["decoding"]["max_tokens"] = int(min(request.max_tokens, 2048))

    provider = cfg["model"]["provider"]
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY environment variable is not set but provider 'openai' was requested.",
        )

    api_log_path = Path("logs") / "api_calls.jsonl"

    try:
        result = ma_generate_tests_validated(
            request.source_code,
            cfg=cfg,
            run_pytest=request.run_pytest,
        )

        governance = result["governance"] or {}

        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "generate-tests-validated",
            "provider": provider,
            "request": {
                "source_len": len(request.source_code),
                "temperature": cfg.get("decoding", {}).get("temperature"),
                "max_tokens": cfg.get("decoding", {}).get("max_tokens"),
                "run_pytest": request.run_pytest,
            },
            "governance": governance,
        }
        _safe_log(log_entry, api_log_path)

        return GenerateTestsValidatedResponse(
            tests=result["tests"],
            prompt=result["prompt"],
            generator_metadata=result["generator_metadata"],
            governance=GovernanceReport(**governance),
        )
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "endpoint": "generate-tests-validated",
            "error": str(e),
            "traceback": tb,
        }
        _safe_log(log_entry, api_log_path)
        raise HTTPException(status_code=500, detail="Internal error while running validated generation.")
