# Railway cron job: SPX chain snapshot -> R2 (see cloud/README.md).
# Build context = python/quantlake (Railway "Root Directory").
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app

# Only what the job imports: the CBOE connector (httpx, polars) and R2 (pyarrow.fs).
RUN pip install --no-cache-dir "polars>=1.44,<2" "pyarrow==24.0.0" "httpx>=0.27,<0.28" "python-dotenv>=1.0,<2"

COPY src/quantlake ./src/quantlake
COPY cloud/chain_job.py ./chain_job.py

CMD ["python", "chain_job.py"]
