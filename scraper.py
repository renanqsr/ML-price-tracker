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
CLIENT_ID     = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
SEARCH_QUERY  = os.getenv("SEARCH_QUERY", "")       # Ex: "iphone 15"
PRODUCT_ID    = os.getenv("PRODUCT_ID", "")          # Ex: "MLB1027172677"
MAX_RESULTS   = int(os.getenv("MAX_RESULTS", "5"))
CSV_FILE      = "data/prices.csv"
CSV_HEADERS   = ["timestamp", "mode", "product_id", "product", "price", "currency", "url"]
ML_API        = "https://api.mercadolibre.com"


# ── Autenticação ──────────────────────────────────────────────────────────────
def get_access_token() -> str:
    """Obtém o access token via Client Credentials."""
    logger.info("Obtendo access token...")
    resp = requests.post(
        f"{ML_API}/oauth/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError("Access token não retornado pela API.")
    logger.info("Token obtido com sucesso.")
    return token


# ── Modo 1: Busca geral ───────────────────────────────────────────────────────
def fetch_by_search(query: str, max_results: int, token: str) -> list[dict]:
    """Busca produtos por termo e retorna os top N resultados."""
    logger.info(f"[BUSCA] query='{query}' | max={max_results}")
    resp = requests.get(
        f"{ML_API}/sites/MLB/search",
        params={"q": query, "limit": max_results},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    results_raw = resp.json().get("results", [])

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
            "mode":       "search",
            "product_id": item_id,
            "product":    title,
            "price":      price,
            "currency":   currency,
            "url":        url,
        })
        logger.info(f"  ✓ [{item_id}] {title[:55]}... → {currency} {price}")

    return records


# ── Modo 2: Produto específico por ID ─────────────────────────────────────────
def fetch_by_id(product_id: str, token: str) -> list[dict]:
    """Busca o preço atual de um produto específico pelo ID do ML."""
    logger.info(f"[ID] Buscando produto: {product_id}")
    resp = requests.get(
        f"{ML_API}/items/{product_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    item = resp.json()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title    = item.get("title", "N/A")
    price    = item.get("price")
    currency = item.get("currency_id", "BRL")
    url      = item.get("permalink", "N/A")

    logger.info(f"  ✓ [{product_id}] {title[:55]}... → {currency} {price}")

    return [{
        "timestamp":  timestamp,
        "mode":       "id",
        "product_id": product_id,
        "product":    title,
        "price":      price,
        "currency":   currency,
        "url":        url,
    }]


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

    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("ML_CLIENT_ID e ML_CLIENT_SECRET são obrigatórios.")

    if not SEARCH_QUERY and not PRODUCT_ID:
        raise ValueError("Configure SEARCH_QUERY e/ou PRODUCT_ID nas variáveis.")

    token = get_access_token()
    all_records = []

    if PRODUCT_ID:
        all_records.extend(fetch_by_id(PRODUCT_ID, token))

    if SEARCH_QUERY:
        all_records.extend(fetch_by_search(SEARCH_QUERY, MAX_RESULTS, token))

    if all_records:
        save_to_csv(all_records)
    else:
        logger.warning("Nenhum dado coletado.")

    logger.info("Scraper finalizado com sucesso.")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()