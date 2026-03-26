import requests
import csv
import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# 1. Configuração de Caminhos (Garante que as pastas existam)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR  = os.path.join(BASE_DIR, "logs")

# Cria as pastas se elas não existirem
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

CSV_FILE = os.path.join(DATA_DIR, "prices.csv")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

# 2. Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 3. Configurações de Busca
SEARCH_QUERY = "iphone 15 128gb"
MAX_RESULTS  = 5
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_prices():
    logger.info(f"Iniciando busca para: {SEARCH_QUERY}")
    url = f"https://lista.mercadolivre.com.br/{SEARCH_QUERY.replace(' ', '-')}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Seleciona os itens da lista
        items = soup.find_all(['li', 'div'], class_='ui-search-result__wrapper', limit=MAX_RESULTS)
        
        results = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in items:
            try:
                # Título
                title_tag = item.find(['h2', 'h3'])
                title = title_tag.text.strip() if title_tag else "N/A"
                
                # Preço (Pega a fração principal)
                price_tag = item.find('span', class_='andes-money-amount__fraction')
                price = price_tag.text.replace('.', '').strip() if price_tag else "0"
                
                # Link e ID
                link_tag = item.find('a', href=True)
                link = link_tag['href'] if link_tag else "N/A"
                prod_id = "MLB" + link.split('/MLB-')[1].split('-')[0] if "/MLB-" in link else "N/A"

                results.append({
                    "timestamp": timestamp,
                    "product_id": prod_id,
                    "product": title,
                    "price": float(price) if price.isdigit() else 0.0,
                    "currency": "BRL",
                    "url": link
                })
                logger.info(f" ✓ Encontrado: {title[:30]}... R$ {price}")
            except:
                continue
        return results
    except Exception as e:
        logger.error(f"Erro na requisição: {e}")
        return []

def save_csv(records):
    # Garante que a pasta existe antes de qualquer coisa
    os.makedirs(DATA_DIR, exist_ok=True)
    
    headers = ["timestamp", "product_id", "product", "price", "currency", "url"]
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        
        # Se o arquivo é novo, escreve o cabeçalho
        if not file_exists:
            writer.writeheader()
            logger.info("Novo arquivo CSV criado com cabeçalhos.")
        
        # Escreve os dados se houver algum
        if records:
            writer.writerows(records)
            logger.info(f"Sucesso! {len(records)} registros adicionados.")
        else:
            logger.warning("Nenhum registro encontrado para salvar, mas o arquivo foi mantido.")

if __name__ == "__main__":
    data = fetch_prices()
    save_csv(data)