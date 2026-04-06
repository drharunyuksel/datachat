"""
Start script — builds frontend, refreshes training data, then launches the server.

Usage: python start.py
"""

import asyncio
import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

WEBCOMPONENT_DIR = os.path.join(os.path.dirname(__file__), "frontends", "webcomponent")


def build_frontend():
    """Build the web component if dist/ is missing."""
    dist_dir = os.path.join(WEBCOMPONENT_DIR, "dist")
    if os.path.isdir(dist_dir):
        print("Frontend already built, skipping. (Delete frontends/webcomponent/dist to rebuild.)")
        return

    print("Building web component...")
    subprocess.run(["npm", "install"], cwd=WEBCOMPONENT_DIR, check=True)
    subprocess.run(["npm", "run", "build"], cwd=WEBCOMPONENT_DIR, check=True)
    print("Frontend build complete.")


async def refresh_training():
    from train import train
    await train(fresh=True)


def start_server():
    import uvicorn
    from main import app

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8084"))
    print(f"\nStarting Vanna server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    build_frontend()
    asyncio.run(refresh_training())
    start_server()
