import requests
import csv
import os
import logging
from datetime import datetime

# Configuração de pastas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

CSV_FILE = os.path.join(DATA_DIR, "prices.csv")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# CONFIGURAÇÕES
SEARCH_QUERY = "iphone 15 128gb"
MAX_RESULTS  = 5

def fetch_prices_api():
    logger.info(f"Buscando via API Pública: {SEARCH_QUERY}")
    # Endpoint oficial de busca (não precisa de Token para buscas públicas)
    url = f"https://api.mercadolibre.com/sites/MLB/search?q={SEARCH_QUERY.replace(' ', '%20')}&limit={MAX_RESULTS}"
    
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # A API retorna os produtos dentro da chave 'results'
        items = data.get("results", [])
        
        for item in items:
            results.append({
                "timestamp": timestamp,
                "product_id": item.get("id"),
                "product": item.get("title"),
                "price": float(item.get("price", 0)),
                "currency": item.get("currency_id"),
                "url": item.get("permalink")
            })
            logger.info(f" ✓ {item.get('title')[:30]}... R$ {item.get('price')}")
            
        return results
    except Exception as e:
        logger.error(f"Erro na API do Mercado Livre: {e}")
        return []

def save_csv(records):
    headers = ["timestamp", "product_id", "product", "price", "currency", "url"]
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        
        if records:
            writer.writerows(records)
            logger.info(f"CSV atualizado com {len(records)} itens.")
        else:
            logger.warning("Nenhum item encontrado pela API.")

if __name__ == "__main__":
    data = fetch_prices_api()
    save_csv(data)