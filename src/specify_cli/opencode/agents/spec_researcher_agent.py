"""
Spec-researcher agent implementation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from specify_cli.services.research_engine import ResearchEngine


class SpecResearcherAgent:
    """Agent for researching specifications"""

    def __init__(self):
        self.research_engine = ResearchEngine()
        self.name = "spec-researcher"
        self.description = "Researches technical topics and provides insights for development"
        self.version = "1.0.0"
        self.author = "spec-kit"
        self.capabilities = ["conduct_research", "analyze_findings", "generate_decision"]
        self.supported_actions = ["research", "analyze", "decide"]
        self.metadata = {
            "category": "research",
            "tags": ["research", "documentation", "analysis"],
            "requires_project": False,
            "input_schema": {
                "research": {
                    "topic": {"type": "string", "required": True},
                    "sources": {"type": "array", "required": False},
                    "spec_id": {"type": "string", "required": False}
                },
                "analyze": {
                    "topic": {"type": "string", "required": True}
                },
                "decide": {
                    "topic": {"type": "string", "required": True},
                    "decision": {"type": "string", "required": True}
                }
            }
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task"""
        action = input_data.get("action", "research")

        if action == "research":
            return self._conduct_research(input_data)
        elif action == "analyze":
            return self._analyze_findings(input_data)
        elif action == "decide":
            return self._generate_decision(input_data)
        else:
            return {
                "error": f"Unknown action: {action}",
                "supported_actions": self.capabilities
            }

    def _conduct_research(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct research on a topic"""
        topic = input_data.get("topic")
        if not topic:
            return {"error": "Topic is required for research"}

        sources = input_data.get("sources", ["web"])
        spec_id = input_data.get("spec_id")

        try:
            research_item = self.research_engine.conduct_research(
                topic=topic,
                sources=sources,
                spec_id=spec_id
            )

            return {
                "success": True,
                "topic": research_item.topic,
                "sources": research_item.source,
                "has_findings": bool(research_item.findings),
                "has_decision": bool(research_item.decision)
            }
        except Exception as e:
            return {"error": f"Failed to conduct research: {str(e)}"}

    def _analyze_findings(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research findings"""
        topic = input_data.get("topic")
        if not topic:
            return {"error": "Topic is required for analysis"}

        research_item = self.research_engine.get_research_item(topic)
        if not research_item:
            return {"error": f"No research found for topic: {topic}"}

        # Analyze findings
        analysis = {
            "topic": research_item.topic,
            "findings_length": len(research_item.findings or ""),
            "alternatives_count": len(research_item.alternatives or []),
            "has_decision": bool(research_item.decision),
            "sources_used": research_item.source
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _generate_decision(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a decision based on research"""
        topic = input_data.get("topic")
        if not topic:
            return {"error": "Topic is required for decision generation"}

        decision = input_data.get("decision")
        if not decision:
            return {"error": "Decision text is required"}

        success = self.research_engine.set_research_decision(topic, decision)

        if success:
            return {
                "success": True,
                "topic": topic,
                "decision": decision
            }
        else:
            return {"error": f"Failed to set decision for topic: {topic}"}

    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.name,
            "status": "active",
            "capabilities": self.capabilities,
            "last_active": datetime.now().isoformat()
        }

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities"""
        return self.capabilities.copy()