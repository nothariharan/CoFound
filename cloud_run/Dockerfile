FROM python:3.11-slim

WORKDIR /app
COPY cloud_run/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/agents ./agents
COPY cloud_run/main.py ./main.py
COPY cloud_run/agent_service.py ./agent_service.py
ENV PYTHONPATH=/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
