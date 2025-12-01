# eval/metrics_utils.py
from sentence_transformers import SentenceTransformer, util
from nltk.translate.bleu_score import sentence_bleu
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def embedding_cosine(a, b):
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    return float(util.cos_sim(emb_a, emb_b).item())

def bleu_score(reference, hypothesis):
    ref_tokens = reference.split()
    hyp_tokens = hypothesis.split()
    return sentence_bleu([ref_tokens], hyp_tokens, weights=(0.5,0.5))
