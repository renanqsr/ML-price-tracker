import requests
import csv
import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# -- Configuração de Pastas --
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

CSV_FILE   = os.path.join(DATA_DIR, "prices.csv")
# Cabeçalhos fixos para o CSV não bagunçar
CSV_HEADERS = ["timestamp", "product_id", "product", "price", "currency", "url"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEARCH_QUERY = "iphone 15 128gb"
MAX_RESULTS  = 5
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def fetch_prices(query, max_results):
    logger.info(f"Buscando: {query}")
    url = f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.find_all('li', class_='ui-search-layout__item', limit=max_results)
        
        records = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in items:
            # Pega o título
            t_tag = item.find(['h2', 'h3'])
            title = t_tag.text.strip() if t_tag else "N/A"
            
            # Pega o preço
            p_tag = item.find('span', class_='andes-money-amount__fraction')
            price = p_tag.text.replace('.', '').strip() if p_tag else "0"
            
            # Pega a URL e o ID
            link_tag = item.find('a', href=True)
            link = link_tag['href'] if link_tag else "N/A"
            prod_id = "MLB" + link.split('/MLB-')[1].split('-')[0] if "/MLB-" in link else "N/A"

            records.append({
                "timestamp": timestamp,
                "product_id": prod_id,
                "product": title,
                "price": float(price) if price.isdigit() else 0.0,
                "currency": "BRL",
                "url": link
            })
            logger.info(f" ✓ {title[:30]}... R$ {price}")
        return records
    except Exception as e:
        logger.error(f"Erro: {e}")
        return []

def save_to_csv(records):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
    logger.info(f"Salvo em: {CSV_FILE}")

if __name__ == "__main__":
    data = fetch_prices(SEARCH_QUERY, MAX_RESULTS)
    if data:
        save_to_csv(data)