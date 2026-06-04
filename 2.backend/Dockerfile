FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Convert the trusted 2020-2025 XLSX files to CSV and load them into Postgres
# on startup. This is the ONLY data path: no seed.py, no synthetic generator,
# no scraper, no external API.
CMD ["sh", "-c", "python -m scripts.load_trusted_yearly && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
