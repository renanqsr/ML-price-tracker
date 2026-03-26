import requests
import csv
import os
import logging
from datetime import datetime

# ── Configuração de logs ──────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Configurações ─────────────────────────────────────────────────────────────
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "")      # Ex: "iphone 15 128gb"
MAX_RESULTS  = int(os.getenv("MAX_RESULTS", "5"))
CSV_FILE     = "data/prices.csv"
CSV_HEADERS  = ["timestamp", "product_id", "product", "price", "currency", "url"]
ML_API       = "https://api.mercadolibre.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept":     "application/json",
}


# ── Busca pública (sem autenticação) ─────────────────────────────────────────
def fetch_by_search(query: str, max_results: int) -> list[dict]:
    """Busca produtos via API pública do ML (sem token)."""
    logger.info(f"[BUSCA] query='{query}' | max={max_results}")

    resp = requests.get(
        f"{ML_API}/sites/MLB/search",
        params={"q": query, "limit": max_results},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    results_raw = resp.json().get("results", [])

    if not results_raw:
        logger.warning("Nenhum resultado encontrado.")
        return []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []

    for item in results_raw:
        title    = item.get("title", "N/A")
        price    = item.get("price")
        currency = item.get("currency_id", "BRL")
        item_id  = item.get("id", "N/A")
        url      = item.get("permalink", "N/A")

        records.append({
            "timestamp":  timestamp,
            "product_id": item_id,
            "product":    title,
            "price":      price,
            "currency":   currency,
            "url":        url,
        })
        logger.info(f"  ✓ [{item_id}] {title[:55]}... → {currency} {price}")

    return records


# ── Salvar CSV ────────────────────────────────────────────────────────────────
def save_to_csv(records: list[dict]) -> None:
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
            logger.info(f"Arquivo criado: {CSV_FILE}")
        writer.writerows(records)

    logger.info(f"{len(records)} registro(s) salvos em {CSV_FILE}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    logger.info("═" * 60)

    if not SEARCH_QUERY:
        raise ValueError("Configure a variável SEARCH_QUERY no GitHub.")

    records = fetch_by_search(SEARCH_QUERY, MAX_RESULTS)

    if records:
        save_to_csv(records)
    else:
        logger.warning("Nenhum dado coletado.")

    logger.info("Scraper finalizado com sucesso.")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()