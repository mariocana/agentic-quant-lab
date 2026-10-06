# ai-desk on a platform (Railway, Fly, Render).
#
# var/ holds the paper account, the risk state and the journal: mount a persistent
# volume at /app/var or every deploy starts the desk from zero.
FROM python:3.12-slim

# node is optional: the preflight uses it to parse the dashboard script before serving
RUN apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY desk ./desk
RUN pip install --no-cache-dir -e .

COPY config ./config
COPY scripts ./scripts
RUN mkdir -p var

ENV HOST=0.0.0.0
# PORT is injected by the platform; DESK_PASSWORD is required on a public bind
EXPOSE 8765
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s CMD \
    python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",8765)}/healthz',timeout=4)"

CMD ["desk", "ui"]
