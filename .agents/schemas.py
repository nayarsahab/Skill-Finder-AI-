from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

class SecurityAssessment(BaseModel):
    approved: bool = Field(description="Whether the skill requested is safe to teach.")
    risk_level: str = Field(description="The risk classification of the requested skill ('high', 'medium', 'low').")
    reason: str = Field(description="Explanation of the safety determination or risks identified.")
    recommended_alternative: Optional[str] = Field(
        default=None,
        description="A safe, beginner-friendly alternative skill to learn if the request is blocked."
    )

class Resource(BaseModel):
    title: str = Field(description="The title of the educational resource.")
    url: str = Field(description="The URL linking to the resource.")
    type: str = Field(description="The type of resource, e.g., 'Course', 'Documentation', 'Video'.")

class WeeklyPlan(BaseModel):
    week_number: int = Field(description="The number of the week (1-4).")
    objective: str = Field(description="The objective or focus area for this week.")
    activities: List[str] = Field(description="A list of safe learning activities or lessons.")
    labs: List[str] = Field(description="Hands-on practice exercises, simulations, or labs.")
    resources: List[Resource] = Field(description="A list of relevant educational resources for this week.")

class SkillCurriculum(BaseModel):
    skill_title: str = Field(description="The name of the skill being taught.")
    safety_checklist: List[str] = Field(description="Safety basics, required tools, and guidelines for safe learning.")
    four_week_plan: List[WeeklyPlan] = Field(description="A detailed four-week learning curriculum.")

    @model_validator(mode='after')
    def validate_plan_length(self) -> 'SkillCurriculum':
        if len(self.four_week_plan) != 4:
            raise ValueError("four_week_plan must contain exactly 4 weeks")
        return self
