import sys
import os
from pathlib import Path

# Set dummy API key to prevent Client initialization errors
os.environ["GEMINI_API_KEY"] = "mock-api-key"

# Add the .agents directory to Python path to enable absolute imports within .agents
agents_dir = Path(__file__).parent.parent.absolute()
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

import pytest
import json
from google.adk.models.base_llm import BaseLlm
from google.adk.models.registry import LLMRegistry
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# Define the Mock LLM class for testing
class TestMockLlm(BaseLlm):
    @classmethod
    def supported_models(cls) -> list[str]:
        return [r"^.*$"]  # Support all models in mock mode

    async def generate_content_async(self, llm_request, stream=False):
        # 1. Identify which agent is calling by looking at the prompt instruction
        instruction = str(llm_request.config.system_instruction or "").lower()
        
        # 2. Get the input query
        user_msg = ""
        if llm_request.contents:
            user_msg = str(llm_request.contents[-1].parts[0].text).lower()

        # Default response
        response_json = "{}"
        
        if "bouncer" in instruction:
            # Handle Security Bouncer mock responses
            if "ignore" in user_msg or "system prompt" in user_msg or "bypass" in user_msg:
                # Injection attempt
                response_json = json.dumps({
                    "approved": False,
                    "risk_level": "high",
                    "reason": "Prompt injection attempt detected.",
                    "recommended_alternative": "Cybersecurity Fundamentals"
                })
            elif "explosives" in user_msg or "bomb" in user_msg:
                response_json = json.dumps({
                    "approved": False,
                    "risk_level": "high",
                    "reason": "Request involves explosives and dangerous materials.",
                    "recommended_alternative": "Chemistry Fundamentals"
                })
            elif "lock picking" in user_msg or "lockpicking" in user_msg:
                response_json = json.dumps({
                    "approved": False,
                    "risk_level": "high",
                    "reason": "Lock picking is a hazardous physical intrusion skill.",
                    "recommended_alternative": "Physical Security Awareness"
                })
            elif "high-voltage" in user_msg or "power-line" in user_msg or "high voltage" in user_msg:
                response_json = json.dumps({
                    "approved": False,
                    "risk_level": "high",
                    "reason": "Electrical grid repair involves hazardous high-voltage procedures.",
                    "recommended_alternative": "Low-Voltage Arduino Robotics"
                })
            elif "offensive cyber" in user_msg or "hacking" in user_msg:
                response_json = json.dumps({
                    "approved": False,
                    "risk_level": "high",
                    "reason": "Cybersecurity offensive actions are prohibited.",
                    "recommended_alternative": "Cybersecurity Fundamentals"
                })
            else:
                # Safe skill
                response_json = json.dumps({
                    "approved": True,
                    "risk_level": "low",
                    "reason": "Requested skill is safe and educational.",
                    "recommended_alternative": None
                })
                
        elif "pathfinder" in instruction:
            # Handle Pathfinder mock responses
            skill_title = "Selected Skill"
            user_msg_lower = user_msg.lower()
            for skill in ["journalism", "python", "retail", "marketing", "data analysis"]:
                if skill in user_msg_lower:
                    skill_title = skill.title()
                    break
            response_json = json.dumps({
                "skill_title": skill_title,
                "safety_checklist": [
                    "Always use a controlled environment.",
                    "Verify code functionality in sandbox."
                ],
                "four_week_plan": [
                    {
                        "week_number": 1,
                        "objective": "Introduction and Foundations",
                        "activities": ["Read foundations", "Setup workspace"],
                        "labs": ["Run basic commands"],
                        "resources": [
                            {"title": "Introduction Guide", "url": "https://wikipedia.org", "type": "Documentation"}
                        ]
                    },
                    {
                        "week_number": 2,
                        "objective": "Guided Practice and Basics",
                        "activities": ["Follow exercises", "Study examples"],
                        "labs": ["Build first script"],
                        "resources": [
                            {"title": "Beginner Course", "url": "https://coursera.org", "type": "Course"}
                        ]
                    },
                    {
                        "week_number": 3,
                        "objective": "Applied Simulation",
                        "activities": ["Run scenarios", "Troubleshoot errors"],
                        "labs": ["Build simulation project"],
                        "resources": [
                            {"title": "Practice Video", "url": "https://youtube.com", "type": "Video"}
                        ]
                    },
                    {
                        "week_number": 4,
                        "objective": "Capstone Project",
                        "activities": ["Design project", "Refine project"],
                        "labs": ["Present Capstone Deliverable"],
                        "resources": [
                            {"title": "Advanced Tutorial", "url": "https://docs.python.org", "type": "Documentation"}
                        ]
                    }
                ]
            })

        yield LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=response_json)]
            ),
            turn_complete=True,
            partial=False
        )

# Monkeypatch LLMRegistry.resolve to always return TestMockLlm
original_resolve = LLMRegistry.resolve
LLMRegistry.resolve = lambda model: TestMockLlm
