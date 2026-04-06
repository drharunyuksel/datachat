# DataChat

Self-hosted text-to-SQL chat interface. Ask questions in natural language, get SQL queries, results, and charts.

Built on [Vanna 2.0](https://github.com/vanna-ai/vanna) (MIT license, archived March 2026). This fork adds:

- Serialization fix for wide tables with complex data types (#1054)
- Table/JSON toggle for query results
- Database schema sidebar (table explorer)
- PostgreSQL system prompt for correct SQL dialect
- Combined train + start script

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
| `python main.py` | Start server only (uses existing training data) |
| `python train.py --fresh` | Re-train schema without starting server |

## License

MIT — see [LICENSE](LICENSE) for details.

Original project: [vanna-ai/vanna](https://github.com/vanna-ai/vanna) by Zain Hoda.
