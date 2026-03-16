#!/usr/bin/env python3
"""Dev launcher for uvicorn — compatible with preview_start sandbox."""
import sys

# Replace any empty-string entry (relative cwd) with the absolute backend path.
# python3 script.py sets sys.path[0] to the script's directory (absolute),
# so this is usually a no-op, but guards against edge cases.
_BACKEND = "/Users/tgt/Documents/GitHub/saas_impacto/backend"
sys.path[:] = [p or _BACKEND for p in sys.path]

from app.main import app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio", http="h11")
