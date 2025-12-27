# generate_tests.py
import os
import json
import time
import re
import argparse
from pathlib import Path
import yaml
from prompts import build_prompt
from tqdm import tqdm

# OpenAI new SDK import (optional - handled gracefully)
try:
    from openai import OpenAI
    # also import top-level openai to access exception types if available
    import openai as _openai
except Exception:
    OpenAI = None
    _openai = None

# Transformers (HF) optional import handled later
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
except Exception:
    AutoTokenizer = None

def load_config(cfg_path="config.yaml"):
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)

# Lazy-initialized OpenAI client
_client = None
def init_openai_client(cfg=None):
    global _client
    if _client is not None:
        return _client
    if OpenAI is None:
        raise RuntimeError("openai library is not installed. Run: pip install --upgrade openai")
    # The OpenAI() client will read OPENAI_API_KEY from environment by default.
    _client = OpenAI()
    return _client

def call_openai(prompt, cfg):
    """
    Uses the new OpenAI client (client.chat.completions.create(...))
    Returns (generated_text, raw_response_object)
    """
    model = cfg["model"]["openai_model"]
    params = cfg.get("decoding", {})

    client = init_openai_client(cfg)

    # Build kwargs for the SDK call
    call_kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": params.get("temperature", 0.0),
        "max_tokens": params.get("max_tokens", 512),
        "top_p": params.get("top_p", 0.95),
    }

    # Remove None values
    call_kwargs = {k: v for k, v in call_kwargs.items() if v is not None}

    resp = client.chat.completions.create(**call_kwargs)

    # Extract generated text
    gen_text = ""
    try:
        choice0 = resp.choices[0]
        if isinstance(choice0, dict):
            gen_text = choice0.get("message", {}).get("content") or choice0.get("text", "")
        else:
            try:
                gen_text = choice0.message["content"]
            except Exception:
                gen_text = getattr(choice0, "text", "") or str(choice0)
    except Exception:
        try:
            gen_text = str(resp)
        except Exception:
            gen_text = ""

    return gen_text, resp

def call_openai_with_retries(prompt, cfg, max_retries=5, initial_backoff=1.0, max_backoff=60.0):
    """
    Wrapper around `call_openai` that retries on rate limit / transient errors.
    Returns (generated_text, raw_response)
    """
    attempt = 0
    while True:
        try:
            return call_openai(prompt, cfg)
        except Exception as e:
            attempt += 1
            msg = str(e)
            if "quota" in msg.lower() or "insufficient_quota" in msg.lower():
                raise RuntimeError(
                    "OpenAI quota exhausted: "
                    "You exceeded your current quota. Check your plan/billing or set a different provider.\n"
                    "Original error: " + msg
                ) from e
            if attempt >= max_retries:
                raise RuntimeError(f"OpenAI request failed after {attempt} attempts: {msg}") from e
            backoff = min(max_backoff, initial_backoff * (2 ** (attempt - 1)))
            jitter = backoff * 0.1
            sleep_t = backoff + (jitter * (0.5 - (time.time() % 1)))
            print(f"OpenAI call failed (attempt {attempt}/{max_retries}): {msg}. Retrying in {sleep_t:.1f}s...")
            time.sleep(sleep_t)

def call_hf(prompt, cfg, hf_pipe=None):
    """
    HF generation call that removes truncation and temperature warnings
    """
    decoding = cfg.get("decoding", {})
    max_new_tokens = decoding.get("max_tokens", 512)
    temperature = decoding.get("temperature", 0.0)
    do_sample = temperature > 0.0

    if hf_pipe is None:
        model_name = cfg["model"]["hf_model"]
        hf_pipe = pipeline("text-generation", model=model_name, device=-1)

    out = hf_pipe(
        prompt,
        max_new_tokens=max_new_tokens,
        truncation=True,          # remove truncation warning
        do_sample=do_sample,
        temperature=temperature,  # remove temperature warning
        return_full_text=False    # only return generated continuation
    )

    if isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict):
        return out[0].get("generated_text", "") or out[0].get("text", ""), out
    return (out[0] if out else ""), out

def log_jsonl(entry, jsonl_path):
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _mock_generate_tests_from_source(func_src, prompt, cfg):
    """Lightweight fallback generator that creates simple pytest tests.

    Used when cfg["model"]["provider"] == "mock" to avoid loading large models.
    """
    match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", func_src)
    func_name = match.group(1) if match else "func_under_test"
    tests = (
        "import pytest\n\n\n"
        f"# Mock-generated tests for {func_name}\n\n"
        f"def test_{func_name}_simple_case():\n"
        "    # TODO: replace with project-specific assertions\n"
        "    assert True\n"
    )
    raw = {"provider": "mock", "note": "mock generator used (no external model loaded)"}
    return tests, raw

def generate_tests_for_source(func_src, cfg):
    """
    Helper to generate tests for a single function/module source string.
    Returns (generated_text, prompt, metadata_dict).
    """
    prompt = build_prompt(
        func_src,
        include_examples=cfg.get("prompt", {}).get("few_shot", False),
        n_examples=cfg.get("prompt", {}).get("examples", 0),
    )
    start = time.time()
    provider = cfg["model"]["provider"]
    hf_available = bool(cfg["model"].get("hf_model"))
    raw = None

    if provider == "openai":
        try:
            gen_text, raw = call_openai_with_retries(prompt, cfg)
        except RuntimeError as e:
            if hf_available:
                try:
                    gen_text, raw = call_hf(prompt, cfg, None)
                except Exception as hf_e:
                    raise RuntimeError(f"HF fallback failed: {hf_e}") from hf_e
            else:
                raise
    elif provider == "hf":
        gen_text, raw = call_hf(prompt, cfg, None)
    elif provider == "mock":
        gen_text, raw = _mock_generate_tests_from_source(func_src, prompt, cfg)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")

    duration = time.time() - start
    metadata = {
        "provider": provider,
        "model": cfg["model"].get("openai_model") or cfg["model"].get("hf_model"),
        "duration_s": duration,
        "raw_preview": str(raw)[:2000],
    }
    return gen_text, prompt, metadata

def main(cfg_path="config.yaml"):
    cfg = load_config(cfg_path)
    data_dir = Path(cfg["dataset"]["functions_dir"])
    out_dir = Path("data/generated_tests")
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(cfg["logging"]["jsonl_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    files = list(data_dir.glob("*.py"))
    hf_pipe = None
    hf_available = bool(cfg["model"].get("hf_model"))
    provider = cfg["model"]["provider"]

    if provider == "hf":
        from transformers import pipeline as _pipeline
        hf_pipe = _pipeline("text-generation", model=cfg["model"]["hf_model"])

    if provider == "openai":
        try:
            init_openai_client(cfg)
        except Exception as e:
            print("OpenAI client initialization failed:", str(e))
            print("Make sure 'openai' package is installed and OPENAI_API_KEY environment variable is set.")
            return

    for f in tqdm(files):
        func_src = f.read_text()
        prompt = build_prompt(func_src, include_examples=cfg["prompt"].get("few_shot", False),
                              n_examples=cfg["prompt"].get("examples", 0))
        start = time.time()
        if provider == "openai":
            try:
                gen_text, raw = call_openai_with_retries(prompt, cfg)
            except RuntimeError as e:
                print("OpenAI request failed:", str(e))
                if hf_available:
                    print("Falling back to HF provider specified in config (`model.hf_model`). Trying HF generation...")
                    try:
                        if hf_pipe is None:
                            from transformers import pipeline as _pipeline
                            hf_pipe = _pipeline("text-generation", model=cfg["model"]["hf_model"])
                        gen_text, raw = call_hf(prompt, cfg, hf_pipe)
                    except Exception as hf_e:
                        print("HF fallback failed:", str(hf_e))
                        print("Stopping due to both OpenAI and HF failures.")
                        return
                else:
                    print("No HF model configured to fall back to. Check `config.yaml` to set `model.hf_model` or resolve OpenAI billing.")
                    return
        elif provider == "hf":
            gen_text, raw = call_hf(prompt, cfg, hf_pipe)
        elif provider == "mock":
            gen_text, raw = _mock_generate_tests_from_source(func_src, prompt, cfg)
        else:
            raise RuntimeError(f"Unknown provider: {provider}")

        duration = time.time() - start
        out_file = out_dir / (f.stem + "_test.py")
        out_file.write_text(gen_text)
        entry = {
            "source_file": str(f),
            "prompt": prompt,
            "generated": gen_text,
            "provider": cfg["model"]["provider"],
            "model": cfg["model"].get("openai_model") or cfg["model"].get("hf_model"),
            "raw": str(raw)[:4000],
            "duration_s": duration,
            "timestamp": time.time()
        }
        log_jsonl(entry, str(log_path))
    print("Done. Generated tests in", out_dir)

if __name__ == "__main__":
    main()
