FROM node:20-slim AS node_base

RUN npm install -g mongodb-mcp-server@0.3.0

FROM python:3.11-slim

WORKDIR /app

COPY --from=node_base /usr/local/bin/mongodb-mcp-server /usr/local/bin/mongodb-mcp-server
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV USE_MONGODB_MCP=true

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
