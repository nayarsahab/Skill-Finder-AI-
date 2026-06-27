from google.adk import Workflow, Context
from google.adk.workflow import node
from typing import Any, List
from pydantic import BaseModel

from schemas import SecurityAssessment, SkillCurriculum, Resource
from security_bouncer import security_bouncer
from pathfinder import pathfinder
from skills.web_search.search import search_resources

class WorkflowState(BaseModel):
    user_query: str = ""

import json
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "cache.json"

def get_cached_assessment(query: str) -> SecurityAssessment | None:
    query_clean = query.strip().lower()
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            if query_clean in cache:
                return SecurityAssessment.model_validate(cache[query_clean])
    except Exception:
        pass
    return None

def save_assessment_to_cache(query: str, assessment: SecurityAssessment) -> None:
    query_clean = query.strip().lower()
    cache = {}
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
    cache[query_clean] = assessment.model_dump()
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except Exception:
        pass

@node(rerun_on_resume=True)
async def bouncer_node(ctx: Context, node_input: Any) -> SecurityAssessment:
    """Function node that wraps security_bouncer agent to propagate route routing."""
    query = str(node_input)
    cached = get_cached_assessment(query)
    if cached:
        print(f"\n[CACHE HIT] Safety check loaded from cache for query: '{query}'")
        ctx.route = bool(cached.approved)
        return cached

    assessment = await ctx.run_node(security_bouncer, node_input)
    if isinstance(assessment, dict):
        assessment = SecurityAssessment.model_validate(assessment)
    ctx.route = bool(assessment.approved)
    
    # Save to local cache
    save_assessment_to_cache(query, assessment)
    return assessment

def web_search_node(ctx: Context, node_input: Any) -> List[dict]:
    """Function node that executes the custom web search skill."""
    query = ctx.state.get("user_query", "")
    resources = search_resources(query)
    return [r.model_dump() for r in resources]

def remediation_node(ctx: Context, node_input: Any) -> SecurityAssessment:
    """Function node that terminates the workflow and returns the blocked SecurityAssessment."""
    # node_input is the output from security_bouncer, which is a SecurityAssessment
    return node_input

# Define the DAG workflow
workflow = Workflow(
    name="skill_finder_workflow",
    state_schema=WorkflowState,
    edges=[
        ("START", bouncer_node),
        (bouncer_node, {
            True: web_search_node,
            False: remediation_node
        }),
        (web_search_node, pathfinder)
    ]
)
