# eval/metrics_utils.py
from typing import Optional
from nltk.translate.bleu_score import sentence_bleu
import numpy as np

_st_model = None
_st_util = None
_st_available: Optional[bool] = None


def _load_st_model():
    global _st_model, _st_util, _st_available
    if _st_available is False:
        return None, None
    if _st_model is not None and _st_util is not None:
        return _st_model, _st_util
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
        _st_util = util
        _st_available = True
        return _st_model, _st_util
    except Exception:
        _st_available = False
        _st_model = None
        _st_util = None
        return None, None


def embedding_cosine(a: str, b: str) -> Optional[float]:
    model, util = _load_st_model()
    if model is None or util is None:
        return None
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb_a, emb_b).item())


def bleu_score(reference: str, hypothesis: str) -> float:
    ref_tokens = reference.split()
    hyp_tokens = hypothesis.split()
    return sentence_bleu([ref_tokens], hyp_tokens, weights=(0.5, 0.5))
