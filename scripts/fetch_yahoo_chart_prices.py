import argparse
import datetime
import json
import logging
import time
from pathlib import Path
import requests
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DEFAULT_TICKERS = [
    "AEFES", "ARCLK", "ASTOR", "BRSAN", "BTCIM", "CANTE", "CCOLA", "CIMSA", 
    "DOAS", "DSTKF", "ENKAI", "GUBRF", "HEKTS", "KONTR", "KRDMD", "KUYAS", 
    "MAVI", "MGROS", "MIATK", "OYAKC", "PASEU", "PETKM", "PGSUS", "SASA", 
    "TAVHL", "TRALT", "TRMET", "TSKB", "TURSG", "ULKER", "THYAO", "ASELS", 
    "BIMAS", "EREGL", "FROTO", "TUPRS", "SISE", "TCELL", "TTKOM", "TOASO"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def fetch_with_backoff(url, params, headers, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "Not Found (404)"}
            elif response.status_code == 429:
                logging.warning(f"Rate limited (429). Retrying... {attempt+1}/{max_retries}")
            else:
                logging.warning(f"Error {response.status_code}. Retrying... {attempt+1}/{max_retries}")
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request exception: {e}. Retrying... {attempt+1}/{max_retries}")
        
        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
        time.sleep(2 ** attempt)
        
    return {"error": "Max retries reached"}

def find_year_end_price(result, target_year):
    timestamps = result.get('timestamp', [])
    if not timestamps:
        return None, None, None, None
        
    quote = result.get('indicators', {}).get('quote', [{}])[0]
    closes = quote.get('close', [])
    
    adjclose_dict = result.get('indicators', {}).get('adjclose', [{}])[0]
    adjcloses = adjclose_dict.get('adjclose', [])
    
    currency = result.get('meta', {}).get('currency', None)
    
    target_date = datetime.date(target_year, 12, 31)
    
    best_idx = -1
    best_date = None
    
    for i, ts in enumerate(timestamps):
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
        if dt <= target_date:
            if i < len(closes) and closes[i] is not None:
                if best_date is None or dt > best_date:
                    best_date = dt
                    best_idx = i
                    
    if best_idx != -1:
        c = closes[best_idx]
        ac = adjcloses[best_idx] if best_idx < len(adjcloses) else c
        return best_date.strftime('%Y-%m-%d'), c, ac, currency
        
    return None, None, None, currency

def main():
    parser = argparse.ArgumentParser(description="Fetch year-end daily close prices from Yahoo Finance Chart API.")
    parser.add_argument("--start-year", type=int, required=True, help="Start year (e.g., 2020)")
    parser.add_argument("--end-year", type=int, required=True, help="End year (e.g., 2025)")
    parser.add_argument("--tickers", type=str, nargs='+', default=DEFAULT_TICKERS, help="List of BIST tickers")
    parser.add_argument("--force", action="store_true", help="Overwrite existing raw JSON files")
    
    args = parser.parse_args()
    
    start_year = args.start_year
    end_year = args.end_year
    tickers = args.tickers
    force = args.force
    
    raw_dir = Path("data/trusted_raw/prices/yahoo_chart_raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_dir = Path("data/trusted_raw/prices")
    csv_path = output_dir / "yahoo_year_end_prices.csv"
    report_path = output_dir / "yahoo_year_end_prices_report.md"
    
    results = []
    success_count = 0
    fail_count = 0
    skipped_count = 0
    
    for year in range(start_year, end_year + 1):
        for ticker in tickers:
            symbol = f"{ticker}.IS"
            json_file = raw_dir / f"{symbol}_{year}.json"
            
            # Idempotency check
            raw_data = None
            if json_file.exists() and not force:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        raw_data = json.load(f)
                    skipped_count += 1
                except Exception:
                    pass
            
            if not raw_data:
                # Fetch from API
                p1 = int(datetime.datetime(year, 12, 20, tzinfo=datetime.timezone.utc).timestamp())
                p2 = int(datetime.datetime(year + 1, 1, 10, tzinfo=datetime.timezone.utc).timestamp())
                
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {
                    "period1": p1,
                    "period2": p2,
                    "interval": "1d",
                    "events": "history",
                    "includeAdjustedClose": "true"
                }
                
                logging.info(f"Fetching {symbol} for {year}...")
                raw_data = fetch_with_backoff(url, params, HEADERS)
                
                # Sleep 0.5s to be polite
                time.sleep(0.5)
                
                # Save raw JSON
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(raw_data, f, indent=2)
            
            # Process data
            status = "success"
            error_msg = None
            price_date, close_price, adj_close_price, currency = None, None, None, None
            
            if "error" in raw_data and raw_data["error"] is not None:
                # Sometimes Yahoo returns error as an object inside "chart" or direct
                if isinstance(raw_data.get("chart", {}).get("error"), dict):
                    err_desc = raw_data["chart"]["error"].get("description", "Unknown error")
                    error_msg = f"API Error: {err_desc}"
                else:
                    error_msg = str(raw_data.get("error"))
                status = "error"
            elif "chart" in raw_data and "result" in raw_data["chart"] and raw_data["chart"]["result"]:
                result = raw_data["chart"]["result"][0]
                price_date, close_price, adj_close_price, currency = find_year_end_price(result, year)
                
                if close_price is None:
                    status = "error"
                    error_msg = "No valid close price found before Dec 31"
            else:
                status = "error"
                error_msg = "Invalid response format or empty result"
                
            if status == "success":
                success_count += 1
            else:
                fail_count += 1
                
            results.append({
                "ticker": ticker,
                "yahoo_symbol": symbol,
                "year": year,
                "target_date": f"{year}-12-31",
                "price_date": price_date,
                "close": close_price,
                "adjclose": adj_close_price,
                "currency": currency,
                "source": "yahoo_chart_api",
                "status": status,
                "error": error_msg
            })

    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)
    logging.info(f"Saved results to {csv_path}")
    
    # Generate Report
    report_content = f"# Yahoo Finance Year-End Prices Report\n\n"
    report_content += f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report_content += f"**Parameters:**\n"
    report_content += f"- Start Year: {start_year}\n"
    report_content += f"- End Year: {end_year}\n"
    report_content += f"- Tickers Count: {len(tickers)}\n\n"
    
    report_content += f"## Summary\n"
    report_content += f"- **Total Records:** {len(results)}\n"
    report_content += f"- **Successful:** {success_count}\n"
    report_content += f"- **Failed/Missing:** {fail_count}\n"
    report_content += f"- **Skipped (API fetch):** {skipped_count} (Read from cache)\n\n"
    
    if fail_count > 0:
        report_content += f"## Errors & Missing Data\n"
        report_content += "| Ticker | Year | Error |\n"
        report_content += "|---|---|---|\n"
        for r in results:
            if r["status"] == "error":
                report_content += f"| {r['ticker']} | {r['year']} | {r['error']} |\n"
                
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    logging.info(f"Saved report to {report_path}")

if __name__ == "__main__":
    main()
