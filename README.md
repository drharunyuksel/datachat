# DataChat

Self-hosted text-to-SQL chat interface. Ask questions in natural language, get SQL queries, results, and charts.

Built on [Vanna 2.0](https://github.com/vanna-ai/vanna) (MIT license, archived March 2026). This fork adds:

- Serialization fix for wide tables with complex data types (#1054)
- Table/JSON toggle for query results
- Database schema sidebar (table explorer)
- PostgreSQL system prompt for correct SQL dialect
- Auto-build frontend on first run
- Multi-database support via `--database` flag
- Combined train + start script

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) (for building the web component frontend on first run)

## Setup

```bash
# Create virtualenv
uv venv .venv --python 3.12
source .venv/bin/activate

# Install
uv pip install -e ".[gemini,postgres,chromadb,fastapi]" python-dotenv

# Configure
cp .env.example .env
# Edit .env with your API keys and database credentials

# Start (trains on schema then launches server)
python start.py
```

Open http://localhost:8084

## Usage

- Click a table in the schema sidebar to expand its columns
- Double-click a table name to insert it into the chat input
- Ask natural language questions — SQL is generated and executed automatically

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |
| `GEMINI_MODEL` | Model name (default: `gemini-2.5-flash`) |
| `POSTGRES_HOST` | PostgreSQL host |
| `POSTGRES_PORT` | PostgreSQL port (default: 5432) |
| `POSTGRES_DATABASE` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |

## Scripts

| Script | Purpose |
|--------|---------|
| `python start.py` | Refresh schema + start server |
| `python start.py --database mydb` | Override the database from `.env` |
| `python start.py --list-databases` | List available PostgreSQL databases |
| `python main.py` | Start server only (uses existing training data) |
| `python train.py --fresh` | Re-train schema without starting server |
| `python train.py --database mydb` | Train schema for a specific database |

### Switching databases

The default database is set via `POSTGRES_DATABASE` in `.env`. To connect to a different database without editing `.env`, use the `--database` flag:

```bash
# See which databases are available
python start.py --list-databases

# Start with a different database
python start.py --database analytics
```

This overrides the database for both schema training and the running server.

## License

MIT — see [LICENSE](LICENSE) for details.

Original project: [vanna-ai/vanna](https://github.com/vanna-ai/vanna) by Zain Hoda.
