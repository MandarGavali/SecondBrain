import os
import sys
from pathlib import Path

# Make `import secondbrain` work without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Unit tests never call Gemini, Qdrant, MongoDB or Redis; a placeholder key
# only satisfies code paths that check the variable is set.
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")
os.environ.setdefault("UPLOAD_MODE", "sync")
