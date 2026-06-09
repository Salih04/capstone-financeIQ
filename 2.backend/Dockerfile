FROM python:3.12-slim

WORKDIR /app

COPY 2.backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY 2.backend/ .
COPY data/ /data/
COPY 3.Datasets/ /3.Datasets/
COPY experiments/ /experiments/
COPY research_agent_training/ /research_agent_training/

ENV TRUSTED_OUT_DIR=/data/trusted
ENV TRUSTED_COMBINED_CSV=/data/trusted/stocks_2020_2025.csv

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]