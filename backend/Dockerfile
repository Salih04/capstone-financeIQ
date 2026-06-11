FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ ./data/
COPY experiments/ ./experiments/
COPY research_agent_training/ ./research_agent_training/

ENV TRUSTED_DATASETS_DIR=/app/data/raw/yearly_xlsx
ENV TRUSTED_OUT_DIR=/app/data/trusted
ENV TRUSTED_COMBINED_CSV=/app/data/trusted/stocks_2020_2025.csv
ENV RESEARCH_REPO_ROOT=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
