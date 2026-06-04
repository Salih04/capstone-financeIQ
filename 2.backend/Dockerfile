FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Load ONLY the trusted source (quarterly_fundamentals_2025.csv) on startup.
# The old `python seed.py` step pulled data from xlsx + a synthetic generator
# (now in unnecessary/) and produced the incorrect/jumbled DB state.
CMD ["sh", "-c", "python -m scripts.load_trusted_fundamentals && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
