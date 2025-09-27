import random

class RankerAgent:
    def __init__(self):
        pass

    def rank_test_cases(self, test_cases: list, top_n: int = 10):
        # Har test case ko random priority do (dummy logic)
        scored = [{"test": t, "score": random.randint(1, 100)} for t in test_cases]

        # Score ke hisaab se sort
        scored = sorted(scored, key=lambda x: x["score"], reverse=True)

        # Top N select
        top_tests = [item["test"] for item in scored[:top_n]]

        return top_tests
