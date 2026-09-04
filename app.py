"""ModelScope Gradio launcher bridge for the FastAPI application."""
from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "7860")),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
