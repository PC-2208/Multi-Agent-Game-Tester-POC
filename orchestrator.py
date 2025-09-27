import os, json, uuid, asyncio
from datetime import datetime
from typing import List, Dict
from executor_simple import ExecutorAgent
from agents.analyzer_agent import AnalyzerAgent

class OrchestratorAgent:
    def __init__(self, max_concurrent_executors: int = 3):
        self.max_concurrent_executors = max_concurrent_executors
        self.analyzer = AnalyzerAgent()
    
    async def run_tests_async(self, tests: List[Dict]) -> str:
        """Orchestrate execution of multiple test cases with multiple executor agents"""
        run_id = uuid.uuid4().hex[:8]
        run_dir = f"runs/{run_id}"
        os.makedirs(run_dir, exist_ok=True)
        
        print(f"Starting test run {run_id} with {len(tests)} tests")
        
        # Create multiple executor agents
        executors = [ExecutorAgent(f"executor_{i}") for i in range(self.max_concurrent_executors)]
        
        # Execute tests with load balancing
        results = await self._execute_tests_with_agents(tests, executors, run_dir)
        
        # Validate results with analyzer agent
        validated_results = await self._validate_results(results, run_dir)
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(run_id, tests, validated_results, run_dir)
        
        # Save report
        with open(os.path.join(run_dir, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        print(f"Test run {run_id} completed. Report saved to {run_dir}/report.json")
        return run_id
    
    async def _execute_tests_with_agents(self, tests: List[Dict], executors: List[ExecutorAgent], run_dir: str) -> List[Dict]:
        """Execute tests using multiple agents with load balancing"""
        results = []
        
        # Create semaphore to limit concurrent executions
        semaphore = asyncio.Semaphore(self.max_concurrent_executors)
        
        async def execute_with_semaphore(test, executor):
            async with semaphore:
                return await executor.execute_test(test, run_dir)
        
        # Distribute tests among executors
        tasks = []
        for i, test in enumerate(tests):
            executor = executors[i % len(executors)]  # Round-robin distribution
            task = execute_with_semaphore(test, executor)
            tasks.append(task)
        
        # Execute all tests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "test_id": tests[i].get("id", f"test_{i}"),
                    "status": "ERROR",
                    "error": str(result),
                    "agent_id": "unknown"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _validate_results(self, results: List[Dict], run_dir: str) -> List[Dict]:
        """Validate all test results using the analyzer agent"""
        print("Validating test results...")
        
        validation_tasks = []
        for result in results:
            if result.get("status") != "ERROR":
                task = self.analyzer.validate_test_result(result, run_dir)
                validation_tasks.append(task)
            else:
                validation_tasks.append(asyncio.create_task(self._create_error_validation(result)))
        
        validated_results = await asyncio.gather(*validation_tasks)
        return validated_results
    
    async def _create_error_validation(self, error_result: Dict) -> Dict:
        """Create validation report for error results"""
        return {
            "test_id": error_result.get("test_id", "unknown"),
            "original_result": error_result,
            "validation_score": 0.0,
            "verdict": "CONFIRMED_FAIL",
            "reproducibility_stats": {"reproducibility_rating": "N/A"},
            "triage_notes": f"Test failed with error: {error_result.get('error', 'Unknown error')}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_comprehensive_report(self, run_id: str, original_tests: List[Dict], validated_results: List[Dict], run_dir: str) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(original_tests)
        passed_tests = sum(1 for r in validated_results if r.get("verdict") in ["CONFIRMED_PASS", "LIKELY_PASS"])
        failed_tests = sum(1 for r in validated_results if r.get("verdict") in ["CONFIRMED_FAIL", "LIKELY_FAIL"])
        uncertain_tests = sum(1 for r in validated_results if r.get("verdict") == "UNCERTAIN")
        
        # Calculate average validation scores
        validation_scores = [r.get("validation_score", 0) for r in validated_results if r.get("validation_score") is not None]
        avg_validation_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
        
        # Calculate reproducibility stats
        repro_stats = [r.get("reproducibility_stats", {}) for r in validated_results]
        high_repro = sum(1 for s in repro_stats if s.get("reproducibility_rating") == "HIGH")
        
        report = {
            "run_id": run_id,
            "target": "https://play.ezygamers.com/",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "uncertain": uncertain_tests,
                "pass_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "average_validation_score": avg_validation_score,
                "high_reproducibility_count": high_repro
            },
            "test_results": validated_results,
            "artifacts_location": run_dir,
            "recommendations": self._generate_recommendations(validated_results)
        }
        
        return report
    
    def _generate_recommendations(self, validated_results: List[Dict]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in validated_results if r.get("verdict") in ["CONFIRMED_FAIL", "LIKELY_FAIL"]]
        uncertain_tests = [r for r in validated_results if r.get("verdict") == "UNCERTAIN"]
        
        if failed_tests:
            recommendations.append(f"Investigate {len(failed_tests)} failed test(s) for potential bugs or issues")
        
        if uncertain_tests:
            recommendations.append(f"Review {len(uncertain_tests)} uncertain test(s) for manual validation")
        
        low_repro_tests = [r for r in validated_results 
                          if r.get("reproducibility_stats", {}).get("reproducibility_rating") == "LOW"]
        if low_repro_tests:
            recommendations.append(f"Improve test stability for {len(low_repro_tests)} test(s) with low reproducibility")
        
        if not recommendations:
            recommendations.append("All tests passed successfully with high confidence")
        
        return recommendations

# Backward compatibility function
async def run_tests_async(tests):
    """Backward compatibility function"""
    orchestrator = OrchestratorAgent()
    return await orchestrator.run_tests_async(tests)
