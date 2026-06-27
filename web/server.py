import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Clear Google Cloud project/location variables to prevent GenAI SDK 
# from overriding our developer API key with OAuth/ADC credentials.
for env_key in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "CLOUD_ML_PROJECT_ID", "GOOGLE_GENAI_USE_VERTEXAI"]:
    os.environ.pop(env_key, None)

# Add parent and .agents directory to path
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent
agents_dir = project_root / ".agents"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from google.adk.runners import InMemoryRunner
from graph import workflow
from schemas import SecurityAssessment, SkillCurriculum
from run_local import export_curriculum_to_markdown, save_curriculum_to_cache, get_cached_curriculum

app = FastAPI(title="Skill Finder AI API", version="1.0.0")

# Input model
class GenerateRequest(BaseModel):
    query: str

class ExportRequest(BaseModel):
    curriculum: SkillCurriculum

@app.get("/api/cache")
def list_cache():
    """Retrieve all cached learning paths and safety checks."""
    curriculum_cache_file = agents_dir / "curriculum_cache.json"
    safety_cache_file = agents_dir / "cache.json"
    
    curriculums = {}
    safety_checks = {}
    
    if curriculum_cache_file.exists():
        try:
            with open(curriculum_cache_file, "r", encoding="utf-8") as f:
                curriculums = json.load(f)
        except Exception:
            pass
            
    if safety_cache_file.exists():
        try:
            with open(safety_cache_file, "r", encoding="utf-8") as f:
                safety_checks = json.load(f)
        except Exception:
            pass
            
    # Compile a history list
    history = []
    for query, data in curriculums.items():
        history.append({
            "query": query,
            "title": data.get("skill_title", query.title()),
            "approved": True,
            "type": "curriculum"
        })
        
    for query, data in safety_checks.items():
        # Only add to history if not already in curriculums (which are approved)
        if query not in curriculums:
            history.append({
                "query": query,
                "title": query.title(),
                "approved": data.get("approved", False),
                "type": "safety_check",
                "risk_level": data.get("risk_level", "low"),
                "reason": data.get("reason", ""),
                "alternative": data.get("recommended_alternative", "")
            })
            
    return {"history": history}

@app.post("/api/generate")
async def generate_curriculum(req: GenerateRequest):
    """Executes the curriculum builder graph or retrieves from cache."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # 1. Check curriculum cache first
    cached_curriculum = get_cached_curriculum(query)
    if cached_curriculum:
        # Create a mock approved security assessment for cached items
        bouncer_assessment = SecurityAssessment(
            approved=True,
            risk_level="low",
            reason="Loaded from persistent curriculum cache.",
            recommended_alternative=None
        )
        # Check if MD file exists
        title_slug = "".join(c if c.isalnum() else "_" for c in cached_curriculum.skill_title).strip("_")
        filename = f"CURRICULUM_{title_slug}.md"
        
        # If markdown is missing, recreate it
        if not (project_root / filename).exists():
            export_curriculum_to_markdown(cached_curriculum)
            
        return {
            "source": "cache",
            "bouncer": bouncer_assessment.model_dump(),
            "curriculum": cached_curriculum.model_dump(),
            "filename": filename
        }
        
    # 2. Cache miss: Run the workflow
    runner = InMemoryRunner(agent=workflow)
    try:
        events = await runner.run_debug(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
        
    bouncer_assessment = None
    curriculum = None
    
    for event in events:
        if event.author == "security_bouncer" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    bouncer_assessment = SecurityAssessment.model_validate_json(text)
                except Exception:
                    pass
        if event.author == "pathfinder" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    curriculum = SkillCurriculum.model_validate_json(text)
                except Exception:
                    pass
                    
    # Format responses
    bouncer_data = bouncer_assessment.model_dump() if bouncer_assessment else {
        "approved": False,
        "risk_level": "high",
        "reason": "Security agent failed to evaluate this request.",
        "recommended_alternative": "General Educational Studies"
    }
    
    if curriculum:
        # Save to curriculum cache
        save_curriculum_to_cache(query, curriculum)
        # Export markdown
        filename = export_curriculum_to_markdown(curriculum)
        return {
            "source": "live",
            "bouncer": bouncer_data,
            "curriculum": curriculum.model_dump(),
            "filename": filename
        }
    else:
        # Blocked or workflow failed
        return {
            "source": "live",
            "bouncer": bouncer_data,
            "curriculum": None,
            "filename": None
        }

@app.post("/api/export")
def export_markdown(req: ExportRequest):
    """Manually triggers markdown file export in workspace root."""
    try:
        filename = export_curriculum_to_markdown(req.curriculum)
        if filename:
            return {"status": "success", "filename": filename}
        raise HTTPException(status_code=500, detail="Failed to write markdown file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files
static_path = current_dir / "static"
app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Default to mock key if GEMINI_API_KEY is not defined
    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = "mock-api-key"
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
