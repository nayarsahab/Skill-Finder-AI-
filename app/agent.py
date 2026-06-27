import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (looks for .env in current and parent directories)
load_dotenv()

# Clear Google Cloud project/location variables to prevent GenAI SDK 
# from overriding our developer API key with OAuth/ADC credentials.
for env_key in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "CLOUD_ML_PROJECT_ID", "GOOGLE_GENAI_USE_VERTEXAI"]:
    os.environ.pop(env_key, None)

# Add .agents directory to Python path to import our Capstone logic
agents_dir = Path(__file__).parent.parent / ".agents"
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from google.adk.apps import App
from graph import workflow

# Define root_agent so that agents-cli playground loader can resolve it
root_agent = workflow

app = App(
    name="app",
    root_agent=root_agent
)
