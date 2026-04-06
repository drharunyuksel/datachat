"""
Training script for Vanna — loads DDL, documentation, and example SQL into ChromaDB.

Usage:
    python train.py                      # Load from all configured sources
    python train.py --postgres-only      # Load only PostgreSQL schemas
    python train.py --bigquery-only      # Load only BigQuery schemas
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv

from vanna.integrations.chromadb.agent_memory import ChromaAgentMemory
from vanna.core.tool import ToolContext
from vanna.core.user import User

load_dotenv()


def get_dummy_context(memory: ChromaAgentMemory) -> ToolContext:
    """Create a minimal ToolContext for training operations."""
    user = User(id="trainer", username="trainer", group_memberships=["admin"])
    return ToolContext(
        user=user,
        conversation_id="training",
        request_id="training",
        agent_memory=memory,
        metadata={},
    )


def get_postgres_ddl(connection_string: str) -> list[dict]:
    """Extract table DDL from PostgreSQL via information_schema."""
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get all user tables
    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
    """)
    tables = cursor.fetchall()

    ddl_entries = []
    for table in tables:
        schema = table["table_schema"]
        name = table["table_name"]
        full_name = f"{schema}.{name}" if schema != "public" else name

        # Get column definitions
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default,
                   character_maximum_length, numeric_precision
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, name))
        columns = cursor.fetchall()

        # Build DDL string
        col_defs = []
        for col in columns:
            col_def = f"  {col['column_name']} {col['data_type']}"
            if col["character_maximum_length"]:
                col_def += f"({col['character_maximum_length']})"
            if col["is_nullable"] == "NO":
                col_def += " NOT NULL"
            if col["column_default"]:
                col_def += f" DEFAULT {col['column_default']}"
            col_defs.append(col_def)

        ddl = f"CREATE TABLE {full_name} (\n" + ",\n".join(col_defs) + "\n);"

        ddl_entries.append({
            "content": f"DDL for table {full_name}:\n{ddl}",
            "table": full_name,
        })

    cursor.close()
    conn.close()
    return ddl_entries


def get_bigquery_ddl(project_id: str, cred_file_path: str | None = None) -> list[dict]:
    """Extract table schemas from BigQuery via INFORMATION_SCHEMA."""
    from google.cloud import bigquery
    from google.oauth2 import service_account
    import json

    if cred_file_path:
        with open(cred_file_path, "r") as f:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(f.read()),
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        client = bigquery.Client(project=project_id, credentials=credentials)
    else:
        client = bigquery.Client(project=project_id)

    # List all datasets
    datasets = list(client.list_datasets())
    ddl_entries = []

    for dataset in datasets:
        dataset_id = dataset.dataset_id
        query = f"""
            SELECT table_name, column_name, data_type, is_nullable
            FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
            ORDER BY table_name, ordinal_position
        """
        try:
            rows = list(client.query(query).result())
        except Exception as e:
            print(f"  Skipping {dataset_id}: {e}")
            continue

        # Group by table
        tables: dict[str, list] = {}
        for row in rows:
            tables.setdefault(row.table_name, []).append(row)

        for table_name, columns in tables.items():
            full_name = f"{project_id}.{dataset_id}.{table_name}"
            col_defs = []
            for col in columns:
                col_def = f"  {col.column_name} {col.data_type}"
                if col.is_nullable == "NO":
                    col_def += " NOT NULL"
                col_defs.append(col_def)

            ddl = f"CREATE TABLE `{full_name}` (\n" + ",\n".join(col_defs) + "\n);"
            ddl_entries.append({
                "content": f"DDL for BigQuery table {full_name}:\n{ddl}",
                "table": full_name,
            })

    return ddl_entries


async def train(postgres_only: bool = False, bigquery_only: bool = False, fresh: bool = False):
    memory = ChromaAgentMemory(
        persist_directory="./chroma_data",
        collection_name="vanna_memory",
    )
    ctx = get_dummy_context(memory)

    if fresh:
        print("Clearing old training data...")
        deleted = await memory.clear_memories(context=ctx)
        print(f"  Cleared {deleted} entries")

    total = 0

    # PostgreSQL
    pg_host = os.getenv("POSTGRES_HOST")
    if pg_host and not bigquery_only:
        print("Loading PostgreSQL schemas...")
        pg_conn = (
            f"host={pg_host} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DATABASE')} "
            f"user={os.getenv('POSTGRES_USER')} "
            f"password={os.getenv('POSTGRES_PASSWORD')}"
        )
        entries = get_postgres_ddl(pg_conn)
        for entry in entries:
            await memory.save_text_memory(content=entry["content"], context=ctx)
            print(f"  Saved: {entry['table']}")
        total += len(entries)
        print(f"  Loaded {len(entries)} PostgreSQL tables")

    # BigQuery
    bq_project = os.getenv("BIGQUERY_PROJECT_ID")
    if bq_project and not postgres_only:
        print("Loading BigQuery schemas...")
        bq_cred_file = os.getenv("BIGQUERY_CREDENTIALS_FILE")
        entries = get_bigquery_ddl(bq_project, bq_cred_file)
        for entry in entries:
            await memory.save_text_memory(content=entry["content"], context=ctx)
            print(f"  Saved: {entry['table']}")
        total += len(entries)
        print(f"  Loaded {len(entries)} BigQuery tables")

    # You can add custom documentation and example SQL here:
    # Example:
    # await memory.save_text_memory(
    #     content="The 'orders' table contains all customer orders. "
    #             "Use order_date for time-based filtering.",
    #     context=ctx,
    # )
    # await memory.save_tool_usage(
    #     question="How many orders were placed last month?",
    #     tool_name="run_sql",
    #     args={"sql": "SELECT COUNT(*) FROM orders WHERE order_date >= NOW() - INTERVAL '1 month'"},
    #     context=ctx,
    # )

    print(f"\nDone! Loaded {total} total entries into ChromaDB.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Vanna with database schemas")
    parser.add_argument("--database", help="PostgreSQL database name (overrides POSTGRES_DATABASE from .env)")
    parser.add_argument("--postgres-only", action="store_true", help="Load only PostgreSQL schemas")
    parser.add_argument("--bigquery-only", action="store_true", help="Load only BigQuery schemas")
    parser.add_argument("--fresh", action="store_true", help="Clear old data before loading")
    args = parser.parse_args()

    if args.database:
        os.environ["POSTGRES_DATABASE"] = args.database

    asyncio.run(train(postgres_only=args.postgres_only, bigquery_only=args.bigquery_only, fresh=args.fresh))
