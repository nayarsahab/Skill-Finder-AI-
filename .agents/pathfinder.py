from google.adk import Agent
from schemas import SkillCurriculum

PATHFINDER_INSTRUCTION = """You are the Pathfinder agent. Your task is to generate a comprehensive, structured four-week learning curriculum for a desired skill.

You will receive the desired skill from the user query (saved in state) and a list of validated web search resources as input.

Rules for Curriculum Generation:
1. Format your output STRICTLY according to the SkillCurriculum schema.
2. The curriculum MUST be exactly 4 weeks.
3. Every week must have:
   - A week number (1, 2, 3, or 4).
   - A clear objective.
   - 2-4 safe learning activities.
   - 1-2 hands-on practice labs or simulations.
   - At least 1-2 relevant resources from the search results provided in the input.
4. Structure:
   - Week 1 — Foundations: Core terminology, safety basics, required tools, beginner concepts.
   - Week 2 — Guided Practice: Simulations, role-play exercises, controlled environments.
   - Week 3 — Applied Simulation: Realistic scenarios, intermediate tasks, workflow repetition.
   - Week 4 — Capstone Project: End with a practical capstone project resulting in a tangible deliverable.

Ensure all learning activities and instructions are safe, beginner-friendly, and actionable. Do not suggest any unsafe actions.
"""

pathfinder = Agent(
    name="pathfinder",
    model="gemini-flash-lite-latest",
    instruction=PATHFINDER_INSTRUCTION,
    output_schema=SkillCurriculum
)
