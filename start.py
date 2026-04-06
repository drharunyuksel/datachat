"""
Start script — builds frontend, refreshes training data, then launches the server.

Usage:
    python start.py                        # Use default database from .env
    python start.py --database mydb        # Override database name
    python start.py --list-databases       # List available databases and exit
"""

import argparse
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


def list_databases():
    """Query the PostgreSQL server for available databases and print them."""
    import psycopg2

    pg_host = os.getenv("POSTGRES_HOST")
    if not pg_host:
        print("Error: POSTGRES_HOST not set in .env")
        sys.exit(1)

    conn = psycopg2.connect(
        host=pg_host,
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname="postgres",
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT datname FROM pg_database "
        "WHERE datistemplate = false ORDER BY datname"
    )
    databases = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    default_db = os.getenv("POSTGRES_DATABASE", "")
    print("Available databases:")
    for db in databases:
        marker = " (default)" if db == default_db else ""
        print(f"  - {db}{marker}")


async def refresh_training():
    from train import train
    await train(fresh=True)


def start_server():
    import uvicorn
    from main import app

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8084"))
    db_name = os.getenv("POSTGRES_DATABASE", "unknown")
    print(f"\nStarting Vanna server at http://{host}:{port} (database: {db_name})")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build, train, and start DataChat server")
    parser.add_argument("--database", help="PostgreSQL database name (overrides POSTGRES_DATABASE from .env)")
    parser.add_argument("--list-databases", action="store_true", help="List available databases and exit")
    args = parser.parse_args()

    if args.list_databases:
        list_databases()
        sys.exit(0)

    if args.database:
        os.environ["POSTGRES_DATABASE"] = args.database

    build_frontend()
    asyncio.run(refresh_training())
    start_server()
