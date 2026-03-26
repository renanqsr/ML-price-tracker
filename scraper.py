import requests
import csv
import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup

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

# CONFIGURAÇÕES - Teste com uma busca simples
SEARCH_QUERY = "iphone 15"
MAX_RESULTS  = 5

# User-Agent mais robusto para evitar bloqueio
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_prices():
    logger.info(f"Buscando: {SEARCH_QUERY}")
    url = f"https://lista.mercadolivre.com.br/{SEARCH_QUERY.replace(' ', '-')}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Tenta capturar os cards de produto (Seletores atualizados 2024/2025)
        items = soup.select(".ui-search-result__wrapper", limit=MAX_RESULTS)
        if not items:
            items = soup.find_all('li', class_='ui-search-layout__item', limit=MAX_RESULTS)

        results = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in items:
            try:
                # Busca título
                title_tag = item.select_one(".ui-search-item__title") or item.find(['h2', 'h3'])
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                
                # Busca preço
                price_tag = item.select_one(".andes-money-amount__fraction")
                price = price_tag.get_text(strip=True).replace('.', '') if price_tag else "0"
                
                # Busca Link
                link_tag = item.find('a', href=True)
                link = link_tag['href'] if link_tag else "N/A"
                
                if title != "N/A" and price != "0":
                    results.append({
                        "timestamp": timestamp,
                        "product_id": "MLB" + link.split('/MLB-')[1].split('-')[0] if "/MLB-" in link else "N/A",
                        "product": title,
                        "price": float(price),
                        "currency": "BRL",
                        "url": link
                    })
                    logger.info(f" ✓ {title[:30]}... R$ {price}")
            except Exception as e:
                continue
        
        return results
    except Exception as e:
        logger.error(f"Erro ao acessar ML: {e}")
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
            logger.info(f"Dados gravados: {len(records)} itens.")
        else:
            # Força uma linha de log se não houver dados
            logger.warning("Nenhum dado novo para gravar.")

if __name__ == "__main__":
    data = fetch_prices()
    save_csv(data)