import os
import glob
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEPLOYMENT_ENVIRONMENT = os.getenv("DEPLOYMENT_ENVIRONMENT", "DEPLOYED_SERVICE")
DEBUG = DEPLOYMENT_ENVIRONMENT == "DEBUG"

# Backend URL for OAuth callbacks
DEFAULT_BACKEND_URL = "http://localhost:8000" if DEBUG else "https://diagramik.com"
BACKEND_URL = os.environ.get("BACKEND_URL", DEFAULT_BACKEND_URL)

current_dir = os.path.dirname(__file__)
py_files = glob.glob(os.path.join(current_dir, "*.py"))

for file in py_files:
    module = os.path.basename(file)
    if module == "__init__.py" or module.startswith("_"):
        continue
    module_name = f".{module[:-3]}"
    exec(f"from {module_name} import *", globals())
