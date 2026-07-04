"""
Agentic AI Service — interfaces with Claude (Anthropic API) for reasoning tasks.

Includes 4 core agent capabilities:
1. Generate routing config from plain English (validated with Pydantic).
2. Explain a routing decision in plain English (grounded in actual decision logs).
3. Detect unhealthy vendors from metrics and logs.
4. Recommend a routing strategy based on goals.

Provides a fully functional fallback mode if ANTHROPIC_API_KEY is not set
so that the application can be previewed/demonstrated offline or without key setup.
"""

import json
import logging
from typing import Optional
# pyrefly: ignore [missing-import]
from anthropic import AsyncAnthropic, APIError

from app.config import settings
from app.models.routing import RoutingConfig
from app.models.vendor import VendorConfig

logger = logging.getLogger(__name__)


class AgentService:
    """Service class encapsulating Claude interaction for routing analytics."""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        if self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning(
                "ANTHROPIC_API_KEY not configured. AgentService is running in fallback/mock mode."
            )

    @property
    def is_mock_mode(self) -> bool:
        return self.client is None

    async def generate_config_from_text(self, text: str) -> dict:
        """
        Convert a plain English description of a routing rule into a validated
        RoutingConfig structure.
        """
        prompt = (
            "You are an expert systems engineer. Convert the following routing rule requirement "
            "expressed in plain English into a valid JSON object matching this schema:\n"
            "{\n"
            "  \"capability\": \"string\",\n"
            "  \"strategy\": \"priority\" | \"weighted\" | \"lowest_latency\" | \"lowest_cost\" | \"failover\" | \"round_robin\" | \"feature_based\" | \"health_based\",\n"
            "  \"failover\": boolean\n"
            "}\n\n"
            f"User request: \"{text}\"\n\n"
            "Return ONLY the raw JSON object, without markdown formatting or other explanation."
        )

        if self.is_mock_mode:
            # Fallback mock logic to parse some simple patterns
            lower_text = text.lower()
            strategy = "priority"
            for strat in ["lowest_latency", "feature_based", "health_based", "lowest_cost", "round_robin", "weighted", "failover", "priority"]:
                if strat.replace("_", " ") in lower_text or strat.replace("_", "-") in lower_text or strat in lower_text:
                    strategy = strat
                    break
            capability = "PAN_VERIFICATION"
            if "ocr" in lower_text:
                capability = "OCR"
            elif "sms" in lower_text:
                capability = "SMS"
                
            return {
                "capability": capability,
                "strategy": strategy,
                "failover": "no failover" not in lower_text and "without failover" not in lower_text
            }

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            # Handle potential markdown code blocks returned by LLM
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content.strip())
            # Validate structure
            RoutingConfig(**data)
            return data
        except Exception as e:
            logger.error(f"Claude generate_config_from_text failed: {e}")
            raise ValueError(f"Failed to generate valid routing config: {e}")

    async def explain_decision(self, log_entry: dict) -> str:
        """
        Explain a routing decision to an operator in friendly, concise,
        data-grounded language.
        """
        prompt = (
            "You are an operations dashboard assistant. Explain in plain, friendly English "
            "why this vendor routing decision was made, based on the following routing log entry. "
            "Be concise (2-3 sentences max). Focus on the outcomes of the attempts and the filtering reasons.\n\n"
            f"Log Entry:\n{json.dumps(log_entry, indent=2)}"
        )

        if self.is_mock_mode:
            outcome = log_entry.get("outcome")
            vendor = log_entry.get("vendorUsed")
            reason = log_entry.get("routingReason", "")
            if outcome == "SUCCESS":
                return f"Request was successfully served by {vendor}. Selection was based on: {reason}."
            else:
                return f"Routing failed because all attempted vendors failed. Details: {reason}."

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude explain_decision failed: {e}")
            return f"Error generating explanation: {e}"

    async def detect_unhealthy_vendors(self, metrics: dict, logs: list[dict]) -> list[dict]:
        """
        Scan live metrics and logs to detect anomalies or unhealthy vendors.
        Returns a list of diagnosed issues.
        """
        prompt = (
            "You are a site reliability engineer. Analyze these live vendor performance metrics "
            "and recent decision logs to detect degraded or unhealthy vendors. "
            "Return a JSON list of objects, each containing:\n"
            "- \"vendor\": name of the vendor\n"
            "- \"status\": \"unhealthy\" or \"degraded\"\n"
            "- \"reason\": short explanation of the issue (e.g. high latency, frequent circuit trips, or error spike)\n"
            "- \"action\": recommended operator action\n\n"
            f"Metrics:\n{json.dumps(metrics, indent=2)}\n\n"
            f"Logs:\n{json.dumps(logs, indent=2)}\n\n"
            "Return ONLY the raw JSON list of objects, no surrounding text."
        )

        if self.is_mock_mode:
            issues = []
            for vendor_name, data in metrics.get("metrics", {}).items():
                short = data.get("shortWindow", {})
                cb = data.get("circuitBreaker", {})
                error_rate = short.get("errorRate", 0)
                latency = short.get("latencyP95", 0) or 0
                cb_state = cb.get("state", "CLOSED")

                if cb_state == "OPEN":
                    issues.append({
                        "vendor": vendor_name,
                        "status": "unhealthy",
                        "reason": f"Circuit breaker is OPEN due to repeated failures.",
                        "action": "Investigate vendor API health and endpoints."
                    })
                elif error_rate > 0.2:
                    issues.append({
                        "vendor": vendor_name,
                        "status": "degraded",
                        "reason": f"High error rate detected in metrics window ({round(error_rate*100)}%).",
                        "action": "Monitor vendor traffic and verify API keys."
                    })
                elif latency > 1500:
                    issues.append({
                        "vendor": vendor_name,
                        "status": "degraded",
                        "reason": f"High response latency (p95: {latency}ms).",
                        "action": "Consider adjusting routing weight or timeout limits."
                    })
            return issues

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Claude detect_unhealthy_vendors failed: {e}")
            return []

    async def recommend_strategy(self, goal: str, metrics: dict) -> dict:
        """
        Recommends a routing strategy + fallback rules based on current metrics
        and the operator's primary goal.
        """
        prompt = (
            "You are a systems architect. Recommend the best routing configuration "
            "to achieve this goal based on current vendor metrics:\n"
            f"Goal: \"{goal}\"\n\n"
            f"Current Metrics:\n{json.dumps(metrics, indent=2)}\n\n"
            "Return a JSON object containing:\n"
            "- \"recommendedStrategy\": e.g. \"lowest_cost\" or \"health_based\"\n"
            "- \"justification\": explanation for the choice\n"
            "- \"fallbackSequence\": list of vendor names in attempt order\n"
            "- \"recommendedThresholds\": dict with proposed settings\n\n"
            "Return ONLY the raw JSON object, no surrounding text."
        )

        if self.is_mock_mode:
            lower_goal = goal.lower()
            strategy = "lowest_cost" if "cost" in lower_goal or "cheap" in lower_goal else "lowest_latency"
            if "health" in lower_goal or "reliab" in lower_goal:
                strategy = "health_based"
                
            return {
                "recommendedStrategy": strategy,
                "justification": f"Selected to best satisfy the goal of '{goal}' under current vendor performance constraints.",
                "fallbackSequence": ["VendorB", "VendorA"],
                "recommendedThresholds": {
                    "circuitBreakerFailureThreshold": 5,
                    "circuitBreakerCooldownSeconds": 30
                }
            }

        try:
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Claude recommend_strategy failed: {e}")
            return {}


# Singleton
agent_service = AgentService()
