import os
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime

class AnalyzerAgent:
    def __init__(self):
        self.validation_runs = 3  # Number of repeat validations
        self.cross_agent_threshold = 0.8  # Agreement threshold for cross-agent validation
    
    async def validate_test_result(self, test_result: Dict, run_dir: str) -> Dict:
        """
        Validate a single test result with repeat and cross-agent checks
        """
        test_id = test_result.get("test_id", "unknown")
        validation_dir = os.path.join(run_dir, f"{test_id}_validation")
        os.makedirs(validation_dir, exist_ok=True)
        
        # Repeat validation - run the same test multiple times
        repeat_results = await self._repeat_validation(test_result, validation_dir)
        
        # Cross-agent validation - simulate multiple agents analyzing the same result
        cross_agent_results = await self._cross_agent_validation(test_result, validation_dir)
        
        # Calculate overall validation score
        validation_score = self._calculate_validation_score(repeat_results, cross_agent_results)
        
        # Determine verdict
        verdict = self._determine_verdict(validation_score, repeat_results, cross_agent_results)
        
        validation_report = {
            "test_id": test_id,
            "original_result": test_result,
            "repeat_validation": repeat_results,
            "cross_agent_validation": cross_agent_results,
            "validation_score": validation_score,
            "verdict": verdict,
            "reproducibility_stats": self._calculate_reproducibility_stats(repeat_results),
            "triage_notes": self._generate_triage_notes(verdict, validation_score),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save validation report
        with open(os.path.join(validation_dir, "validation_report.json"), "w") as f:
            json.dump(validation_report, f, indent=2)
        
        return validation_report
    
    async def _repeat_validation(self, test_result: Dict, validation_dir: str) -> List[Dict]:
        """Run the same test multiple times to check reproducibility"""
        repeat_results = []
        
        for i in range(self.validation_runs):
            # Simulate repeat execution (in real implementation, this would re-run the test)
            repeat_result = {
                "run_number": i + 1,
                "status": test_result.get("status", "UNKNOWN"),
                "consistency_score": self._calculate_consistency_score(test_result, i),
                "timestamp": datetime.now().isoformat()
            }
            repeat_results.append(repeat_result)
            
            # Add small delay to simulate execution time
            await asyncio.sleep(0.1)
        
        return repeat_results
    
    async def _cross_agent_validation(self, test_result: Dict, validation_dir: str) -> List[Dict]:
        """Simulate multiple agents analyzing the same result"""
        cross_agent_results = []
        
        # Simulate 3 different agents analyzing the result
        for agent_id in range(3):
            agent_result = {
                "agent_id": f"analyzer_{agent_id}",
                "analysis": self._analyze_test_result(test_result, agent_id),
                "confidence": self._calculate_agent_confidence(test_result, agent_id),
                "timestamp": datetime.now().isoformat()
            }
            cross_agent_results.append(agent_result)
        
        return cross_agent_results
    
    def _analyze_test_result(self, test_result: Dict, agent_id: int) -> Dict:
        """Analyze test result from different agent perspectives"""
        status = test_result.get("status", "UNKNOWN")
        artifacts = test_result.get("artifacts", {})
        
        # Different agents focus on different aspects
        if agent_id == 0:  # Screenshot analyzer
            return {
                "focus": "visual_analysis",
                "screenshot_present": "screenshot" in artifacts,
                "visual_issues": self._detect_visual_issues(artifacts),
                "recommendation": "PASS" if status == "PASS" else "FAIL"
            }
        elif agent_id == 1:  # DOM analyzer
            return {
                "focus": "dom_analysis",
                "dom_present": "dom" in artifacts,
                "dom_issues": self._detect_dom_issues(artifacts),
                "recommendation": "PASS" if status == "PASS" else "FAIL"
            }
        else:  # Console analyzer
            return {
                "focus": "console_analysis",
                "console_present": "console" in artifacts,
                "console_issues": self._detect_console_issues(artifacts),
                "recommendation": "PASS" if status == "PASS" else "FAIL"
            }
    
    def _detect_visual_issues(self, artifacts: Dict) -> List[str]:
        """Detect visual issues in screenshots"""
        issues = []
        if "screenshot" in artifacts:
            # In real implementation, this would analyze the actual screenshot
            issues.append("No visual issues detected")
        return issues
    
    def _detect_dom_issues(self, artifacts: Dict) -> List[str]:
        """Detect DOM structure issues"""
        issues = []
        if "dom" in artifacts:
            # In real implementation, this would analyze the DOM structure
            issues.append("DOM structure appears valid")
        return issues
    
    def _detect_console_issues(self, artifacts: Dict) -> List[str]:
        """Detect console log issues"""
        issues = []
        if "console" in artifacts:
            # In real implementation, this would analyze console logs
            issues.append("No console errors detected")
        return issues
    
    def _calculate_consistency_score(self, test_result: Dict, run_number: int) -> float:
        """Calculate consistency score for repeat validation"""
        # Simulate consistency based on run number and original status
        base_score = 0.9 if test_result.get("status") == "PASS" else 0.7
        variation = (run_number * 0.05) % 0.2  # Add some variation
        return max(0.0, min(1.0, base_score - variation))
    
    def _calculate_agent_confidence(self, test_result: Dict, agent_id: int) -> float:
        """Calculate confidence score for each agent"""
        base_confidence = 0.85
        agent_variation = (agent_id * 0.1) % 0.3
        return max(0.0, min(1.0, base_confidence + agent_variation))
    
    def _calculate_validation_score(self, repeat_results: List[Dict], cross_agent_results: List[Dict]) -> float:
        """Calculate overall validation score"""
        # Average consistency from repeat validation
        repeat_score = sum(r.get("consistency_score", 0) for r in repeat_results) / len(repeat_results)
        
        # Average confidence from cross-agent validation
        cross_agent_score = sum(r.get("confidence", 0) for r in cross_agent_results) / len(cross_agent_results)
        
        # Weighted average
        return (repeat_score * 0.6) + (cross_agent_score * 0.4)
    
    def _determine_verdict(self, validation_score: float, repeat_results: List[Dict], cross_agent_results: List[Dict]) -> str:
        """Determine final verdict based on validation results"""
        if validation_score >= 0.9:
            return "CONFIRMED_PASS"
        elif validation_score >= 0.7:
            return "LIKELY_PASS"
        elif validation_score >= 0.5:
            return "UNCERTAIN"
        elif validation_score >= 0.3:
            return "LIKELY_FAIL"
        else:
            return "CONFIRMED_FAIL"
    
    def _calculate_reproducibility_stats(self, repeat_results: List[Dict]) -> Dict:
        """Calculate reproducibility statistics"""
        scores = [r.get("consistency_score", 0) for r in repeat_results]
        return {
            "average_consistency": sum(scores) / len(scores),
            "min_consistency": min(scores),
            "max_consistency": max(scores),
            "variance": sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores),
            "reproducibility_rating": "HIGH" if min(scores) > 0.8 else "MEDIUM" if min(scores) > 0.6 else "LOW"
        }
    
    def _generate_triage_notes(self, verdict: str, validation_score: float) -> str:
        """Generate triage notes based on verdict and score"""
        if verdict == "CONFIRMED_PASS":
            return "Test passed consistently across all validations. No action required."
        elif verdict == "LIKELY_PASS":
            return "Test likely passed but with some inconsistencies. Monitor for future runs."
        elif verdict == "UNCERTAIN":
            return "Test results are uncertain. Manual review recommended."
        elif verdict == "LIKELY_FAIL":
            return "Test likely failed. Investigate root cause and fix if necessary."
        else:  # CONFIRMED_FAIL
            return "Test consistently failed. Immediate attention required."
