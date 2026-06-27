from google.adk.apps import App
from graph import workflow

app = App(
    name="skill_finder_app",
    root_agent=workflow
)
