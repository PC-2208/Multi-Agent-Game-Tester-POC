from typing import List, Dict

def generate_plan(num: int = 20) -> List[Dict]:
    tests = []
    for i in range(1, num+1):
        tests.append({
            "id": f"tc-{i:03}",
            "title": f"Auto test #{i}",
            "description": "Auto-generated dummy test case for POC",
            "steps": [
                {"action": "goto", "value": "https://play.ezygamers.com/"},
                {"action": "click", "selector": "button"},   # placeholder
                {"action": "assert_text", "selector": "#result", "value": "expected"}
            ],
            "tags": ["math", "poc", "auto"],
            "seed_data": {}
        })
    return tests
