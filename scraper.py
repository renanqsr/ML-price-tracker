import requests
import csv
import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# -- Configuração de logs e arquivos --
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR    = os.path.join(SCRIPT_DIR, "logs")
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
CSV_FILE   = os.path.join(DATA_DIR, "prices.csv")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "scraper.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# -- Configurações --
SEARCH_QUERY = "iphone 15 128gb"
MAX_RESULTS  = 5
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_prices(query: str, max_results: int) -> list[dict]:
    logger.info(f"Buscando no site: '{query}'")
    
    # Monta a URL de busca normal do Mercado Livre
    search_url = f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}"
    
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Erro ao acessar o site: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    # Encontra os blocos de produtos
    items = soup.find_all('li', class_='ui-search-layout__item', limit=max_results)
    
    records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in items:
        try:
            # Extrai título
            title = item.find('h2', class_='ui-search-item__title').text.strip()
            
            # Extrai preço (parte inteira)
            price_fraction = item.find('span', class_='andes-money-amount__fraction').text.replace('.', '')
            
            # Extrai URL
            link = item.find('a', class_='ui-search-link')['href']
            
            # Extrai ID do link (opcional)
            product_id = link.split('/MLB-')[1].split('-')[0] if '/MLB-' in link else "N/A"

            records.append({
                "timestamp": timestamp,
                "product_id": f"MLB{product_id}",
                "product": title,
                "price": float(price_fraction),
                "currency": "BRL",
                "url": link,
            })
            logger.info(f" ✓ {title[:40]}... -> R$ {price_fraction}")
        except Exception as e:
            continue

    return records

def save_to_csv(records: list[dict]) -> None:
    file_exists = os.path.isfile(CSV_FILE)
    headers = ["timestamp", "product_id", "product", "price", "currency", "url"]

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
    logger.info(f"Salvo: {len(records)} itens em {CSV_FILE}")

def main():
    logger.info("="*50)
    data = fetch_prices(SEARCH_QUERY, MAX_RESULTS)
    if data:
        save_to_csv(data)
    logger.info("Fim do processo.")
    logger.info("="*50)

if __name__ == "__main__":
    main()