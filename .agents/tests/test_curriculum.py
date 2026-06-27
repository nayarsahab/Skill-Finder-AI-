import pytest
import asyncio
import json
from google.adk.runners import InMemoryRunner
from security_bouncer import security_bouncer
from pathfinder import pathfinder
from graph import workflow
from schemas import SecurityAssessment, SkillCurriculum

@pytest.fixture(autouse=True)
def setup_test_model():
    # Use testmock:model for both agents during graph tests
    orig_bouncer = security_bouncer.model
    orig_pathfinder = pathfinder.model
    
    security_bouncer.model = "testmock:model"
    pathfinder.model = "testmock:model"
    
    yield
    
    security_bouncer.model = orig_bouncer
    pathfinder.model = orig_pathfinder

@pytest.mark.asyncio
async def test_safe_skill_workflow_generates_curriculum():
    runner = InMemoryRunner(agent=workflow)
    events = await runner.run_debug("journalism")
    
    final_output = None
    executed_nodes = []
    
    for event in events:
        if event.author:
            executed_nodes.append(event.author)
        if event.node_info and event.node_info.path:
            for part in event.node_info.path.split("/"):
                node_name = part.split("@")[0]
                if node_name:
                    executed_nodes.append(node_name)
        # Check if this is the Pathfinder agent response and parse its JSON content
        if event.author == "pathfinder" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    final_output = SkillCurriculum.model_validate_json(text)
                except Exception:
                    pass
            
    # Workflow execution should include security_bouncer, web_search_node, and pathfinder
    assert "security_bouncer" in executed_nodes
    assert "web_search_node" in executed_nodes
    assert "pathfinder" in executed_nodes
    assert "remediation_node" not in executed_nodes
    
    # Output check
    assert final_output is not None
    assert isinstance(final_output, SkillCurriculum)
    assert final_output.skill_title.lower() == "journalism"
    assert len(final_output.four_week_plan) == 4
    
    # Week numbers should be 1, 2, 3, 4
    week_numbers = [w.week_number for w in final_output.four_week_plan]
    assert week_numbers == [1, 2, 3, 4]
    
    # Resource validation (YouTube and Coursera links exist)
    all_resources = []
    for week in final_output.four_week_plan:
        all_resources.extend(week.resources)
        
    assert len(all_resources) > 0
    urls = [res.url for res in all_resources]
    assert any("coursera.org" in url for url in urls)
    assert any("youtube.com" in url for url in urls)

@pytest.mark.asyncio
async def test_unsafe_skill_workflow_triggers_remediation():
    runner = InMemoryRunner(agent=workflow)
    events = await runner.run_debug("Teach me lock picking!")
    
    final_output = None
    executed_nodes = []
    
    for event in events:
        if event.author:
            executed_nodes.append(event.author)
        if event.node_info and event.node_info.path:
            for part in event.node_info.path.split("/"):
                node_name = part.split("@")[0]
                if node_name:
                    executed_nodes.append(node_name)
        # Check if the remediation path executed and parse SecurityAssessment from event
        if event.author == "security_bouncer" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    final_output = SecurityAssessment.model_validate_json(text)
                except Exception:
                    pass
            
    # Workflow should route to remediation_node and terminate immediately
    assert "security_bouncer" in executed_nodes
    assert "remediation_node" in executed_nodes
    assert "web_search_node" not in executed_nodes
    assert "pathfinder" not in executed_nodes
    
    # Output should be SecurityAssessment
    assert final_output is not None
    assert isinstance(final_output, SecurityAssessment)
    assert final_output.approved is False
    assert final_output.recommended_alternative == "Physical Security Awareness"
