"""
Start script — refreshes training data then launches the server.

Usage: python start.py
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


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
    asyncio.run(refresh_training())
    start_server()
