import random
from typing import List, Dict

def rank_tests(tests: List[Dict], top_n: int = 10):
    for t in tests:
        t["_score"] = random.random()  # simple: random score. Replace with LLM later.
    tests_sorted = sorted(tests, key=lambda x: x["_score"], reverse=True)
    return tests_sorted[:top_n]
