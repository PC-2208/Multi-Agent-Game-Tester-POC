import os, json, time, asyncio
from playwright.async_api import async_playwright
from typing import List, Dict
import uuid

class ExecutorAgent:
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"executor_{uuid.uuid4().hex[:8]}"
        self.network_logs = []
    
    async def execute_test(self, test: dict, run_dir: str) -> Dict:
        """Execute a single test case and capture comprehensive artifacts"""
        test_id = test.get("id", "tc-unknown")
        out = {
            "test_id": test_id,
            "agent_id": self.agent_id,
            "status": "ERROR", 
            "artifacts": {},
            "execution_time": 0,
            "steps_executed": [],
            "network_requests": [],
            "performance_metrics": {}
        }
        
        test_dir = os.path.join(run_dir, test_id)
        os.makedirs(test_dir, exist_ok=True)
        
        start_time = time.time()
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Set up comprehensive logging
                console_logs = []
                network_logs = []
                
                page.on("console", lambda msg: console_logs.append({
                    "type": msg.type,
                    "text": msg.text,
                    "timestamp": time.time()
                }))
                
                page.on("request", lambda request: network_logs.append({
                    "type": "request",
                    "url": request.url,
                    "method": request.method,
                    "timestamp": time.time()
                }))
                
                page.on("response", lambda response: network_logs.append({
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "timestamp": time.time()
                }))

                # Execute test steps
                steps_executed = await self._execute_test_steps(page, test, test_dir)
                
                # Capture comprehensive artifacts
                artifacts = await self._capture_artifacts(page, test_dir, console_logs, network_logs)
                
                # Calculate performance metrics
                performance_metrics = await self._capture_performance_metrics(page)
                
                await browser.close()

                execution_time = time.time() - start_time
                
                out.update({
                    "status": "PASS",
                    "artifacts": artifacts,
                    "execution_time": execution_time,
                    "steps_executed": steps_executed,
                    "network_requests": network_logs,
                    "performance_metrics": performance_metrics
                })
                
        except Exception as e:
            out.update({
                "status": "FAIL",
                "error": str(e),
                "execution_time": time.time() - start_time
            })
            
        return out
    
    async def _execute_test_steps(self, page, test: dict, test_dir: str) -> List[Dict]:
        """Execute individual test steps and return execution details"""
        steps_executed = []
        steps = test.get("steps", [])
        
        for i, step in enumerate(steps):
            step_result = {
                "step_number": i + 1,
                "action": step.get("action"),
                "value": step.get("value"),
                "selector": step.get("selector"),
                "timestamp": time.time(),
                "status": "PENDING"
            }
            
            try:
                if step["action"] == "goto":
                    await page.goto(step["value"], timeout=15000)
                    await page.wait_for_timeout(1000)
                    step_result["status"] = "PASS"
                    
                elif step["action"] == "click":
                    if "selector" in step:
                        await page.click(step["selector"])
                        await page.wait_for_timeout(500)
                        step_result["status"] = "PASS"
                    else:
                        step_result["status"] = "SKIP"
                        
                elif step["action"] == "assert_text":
                    if "selector" in step and "value" in step:
                        element = await page.query_selector(step["selector"])
                        if element:
                            text_content = await element.text_content()
                            if step["value"] in text_content:
                                step_result["status"] = "PASS"
                            else:
                                step_result["status"] = "FAIL"
                                step_result["expected"] = step["value"]
                                step_result["actual"] = text_content
                        else:
                            step_result["status"] = "FAIL"
                            step_result["error"] = "Element not found"
                    else:
                        step_result["status"] = "SKIP"
                        
                else:
                    step_result["status"] = "SKIP"
                    step_result["note"] = f"Action '{step['action']}' not implemented"
                    
            except Exception as e:
                step_result["status"] = "ERROR"
                step_result["error"] = str(e)
            
            steps_executed.append(step_result)
            
        return steps_executed
    
    async def _capture_artifacts(self, page, test_dir: str, console_logs: List, network_logs: List) -> Dict:
        """Capture comprehensive artifacts"""
        artifacts = {}
        
        # Screenshot
        screenshot_path = os.path.join(test_dir, "screenshot.png")
        await page.screenshot(path=screenshot_path, full_page=True)
        artifacts["screenshot"] = screenshot_path
        
        # DOM snapshot
        dom_html = await page.content()
        dom_path = os.path.join(test_dir, "dom.html")
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(dom_html)
        artifacts["dom"] = dom_path
        
        # Console logs
        console_path = os.path.join(test_dir, "console.log")
        with open(console_path, "w", encoding="utf-8") as f:
            for log in console_logs:
                f.write(f"[{log['type']}] {log['text']}\n")
        artifacts["console"] = console_path
        
        # Network logs
        network_path = os.path.join(test_dir, "network.json")
        with open(network_path, "w", encoding="utf-8") as f:
            json.dump(network_logs, f, indent=2)
        artifacts["network"] = network_path
        
        # Page title and URL
        artifacts["page_title"] = await page.title()
        artifacts["page_url"] = page.url
        
        return artifacts
    
    async def _capture_performance_metrics(self, page) -> Dict:
        """Capture performance metrics"""
        try:
            # Get performance metrics from the page
            metrics = await page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        load_time: navigation.loadEventEnd - navigation.loadEventStart,
                        dom_content_loaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        first_paint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        first_contentful_paint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    };
                }
            """)
            return metrics
        except Exception as e:
            return {"error": str(e)}

# Backward compatibility function
async def execute_test(test: dict, run_dir: str) -> Dict:
    """Backward compatibility function"""
    executor = ExecutorAgent()
    return await executor.execute_test(test, run_dir)
