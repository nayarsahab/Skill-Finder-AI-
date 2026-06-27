import asyncio
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Clear Google Cloud project/location variables to prevent GenAI SDK 
# from overriding our developer API key with OAuth/ADC credentials.
for env_key in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "CLOUD_ML_PROJECT_ID", "GOOGLE_GENAI_USE_VERTEXAI"]:
    os.environ.pop(env_key, None)

# Add current folder to sys.path to resolve imports correctly
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from google.adk.runners import InMemoryRunner
from graph import workflow
from schemas import SecurityAssessment, SkillCurriculum

CURRICULUM_CACHE_FILE = Path(__file__).parent / "curriculum_cache.json"

def get_cached_curriculum(query: str) -> SkillCurriculum | None:
    query_clean = query.strip().lower()
    if not CURRICULUM_CACHE_FILE.exists():
        return None
    try:
        with open(CURRICULUM_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            if query_clean in cache:
                return SkillCurriculum.model_validate(cache[query_clean])
    except Exception:
        pass
    return None

def save_curriculum_to_cache(query: str, curriculum: SkillCurriculum) -> None:
    query_clean = query.strip().lower()
    cache = {}
    if CURRICULUM_CACHE_FILE.exists():
        try:
            with open(CURRICULUM_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
    cache[query_clean] = curriculum.model_dump()
    try:
        CURRICULUM_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CURRICULUM_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4)
    except Exception:
        pass

async def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter a skill you want to learn: ").strip()

    if not query:
        print("Please enter a valid skill.")
        return

    # Check cache first to avoid re-generating existing files
    cached_curriculum = get_cached_curriculum(query)
    if cached_curriculum:
        title_slug = "".join(c if c.isalnum() else "_" for c in cached_curriculum.skill_title).strip("_")
        filename = f"CURRICULUM_{title_slug}.md"
        if Path(filename).exists():
            print(f"\n[CACHE HIT] Markdown curriculum file already exists: {filename}")
            print(f"Skipping workflow execution. You can view the existing file directly.")
            return
        else:
            print(f"\n[CACHE HIT] Found curriculum in cache. Re-exporting markdown file: {filename}")
            export_curriculum_to_markdown(cached_curriculum)
            print(f"💾 [EXPORT] Curriculum exported to Markdown file: {filename}")
            return

    print(f"\nEvaluating safety and searching learning resources for: '{query}'...")
    runner = InMemoryRunner(agent=workflow)
    
    # Run the workflow
    try:
        events = await runner.run_debug(query)
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        return

    # Process workflow execution events
    bouncer_assessment = None
    curriculum = None
    
    for event in events:
        # Check if the bouncer yielded assessment output
        if event.author == "security_bouncer" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    bouncer_assessment = SecurityAssessment.model_validate_json(text)
                except Exception:
                    pass
        # Check if the pathfinder yielded the curriculum
        if event.author == "pathfinder" and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text:
                try:
                    curriculum = SkillCurriculum.model_validate_json(text)
                except Exception:
                    pass

    # Print Results
    print("\n" + "=" * 50)
    print("               WORKFLOW EXECUTION RESULTS               ")
    print("=" * 50)

    if bouncer_assessment:
        print(f"Safety Check Approved: {bouncer_assessment.approved}")
        print(f"Risk Level: {bouncer_assessment.risk_level.upper()}")
        print(f"Safety Analysis Reason: {bouncer_assessment.reason}")
        if bouncer_assessment.recommended_alternative:
            print(f"Alternative Recommendation: {bouncer_assessment.recommended_alternative}")
    
    if curriculum:
        print("\n" + "-" * 50)
        print(f"📚 Four-Week Learning Curriculum for: {curriculum.skill_title.upper()}")
        print("-" * 50)
        print("\n🔒 SAFETY CHECKLIST:")
        for idx, rule in enumerate(curriculum.safety_checklist, 1):
            print(f"  {idx}. {rule}")

        for week in curriculum.four_week_plan:
            print(f"\n📅 WEEK {week.week_number}: {week.objective}")
            print("  Activities:")
            for act in week.activities:
                print(f"    - {act}")
            print("  Labs/Simulations:")
            for lab in week.labs:
                print(f"    - {lab}")
            print("  Suggested Resources:")
            for res in week.resources:
                print(f"    - {res.title} ({res.type}): {res.url}")
        
        # Export curriculum
        saved_file = export_curriculum_to_markdown(curriculum)
        if saved_file:
            print("\n" + "-" * 50)
            print(f"💾 [EXPORT] Curriculum exported to Markdown file: {saved_file}")
            print("-" * 50)
            # Save the generated curriculum to cache
            save_curriculum_to_cache(query, curriculum)
    else:
        if bouncer_assessment and not bouncer_assessment.approved:
            print("\n❌ Curriculum generation was BLOCKED because the requested skill is hazardous.")
            print(f"👉 Recommended Safe Alternative: {bouncer_assessment.recommended_alternative}")
        else:
            print("\n⚠️ No curriculum was generated. Workflow did not complete the learning path generation.")
    
    print("=" * 50)

def export_curriculum_to_markdown(curriculum: SkillCurriculum) -> str:
    """Exports the generated curriculum to a beautifully formatted Markdown file."""
    # Create a safe filename based on the skill title
    title_slug = "".join(c if c.isalnum() else "_" for c in curriculum.skill_title).strip("_")
    filename = f"CURRICULUM_{title_slug}.md"
    
    lines = [
        f"# 📚 4-Week Learning Curriculum: {curriculum.skill_title.upper()}",
        "",
        "## 🔒 Safety Checklist & Guidelines",
        "Before beginning, please read and follow these safety guidelines:",
        ""
    ]
    for idx, rule in enumerate(curriculum.safety_checklist, 1):
        lines.append(f"  {idx}. {rule}")
    lines.append("")
    
    for week in curriculum.four_week_plan:
        lines.extend([
            f"## 📅 Week {week.week_number}: {week.objective}",
            "",
            "### 📝 Learning Activities",
            ""
        ])
        for act in week.activities:
            lines.append(f"  - {act}")
        lines.extend([
            "",
            "### 🔬 Practical Labs & Simulations",
            ""
        ])
        for lab in week.labs:
            lines.append(f"  - {lab}")
        lines.extend([
            "",
            "### 🔗 Curated Resources",
            ""
        ])
        for res in week.resources:
            lines.append(f"  - **{res.title}** ({res.type}): [{res.url}]({res.url})")
        lines.append("")
        
    content = "\n".join(lines)
    try:
        # Save to current working directory (workspace root)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return filename
    except Exception as e:
        print(f"Error exporting curriculum: {e}")
        return ""

if __name__ == '__main__':
    # Default to a mock API key if none is set, to allow running offline or via simulation
    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = "mock-api-key"
    asyncio.run(main())
