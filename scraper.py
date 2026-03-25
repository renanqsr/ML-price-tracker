import requests
from bs4 import BeautifulSoup
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
SEARCH_QUERY  = os.getenv("SEARCH_QUERY", "")        # Termo de busca geral
PRODUCT_URL   = os.getenv("PRODUCT_URL", "")         # Link direto de um produto
MAX_RESULTS   = int(os.getenv("MAX_RESULTS", "5"))   # Só usado no modo busca
CSV_FILE      = "data/prices.csv"
CSV_HEADERS   = ["timestamp", "mode", "product", "price", "currency", "url"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


# ── Modo 1: Busca geral ───────────────────────────────────────────────────────
def fetch_by_search(query: str, max_results: int) -> list[dict]:
    """Busca os top N produtos no ML por termo de busca."""
    url = f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}"
    logger.info(f"[BUSCA] Acessando: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na requisição (busca): {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("li.ui-search-layout__item")

    if not items:
        logger.warning("[BUSCA] Nenhum item encontrado. Seletor pode ter mudado.")
        return []

    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in items[:max_results]:
        try:
            title_tag = item.select_one("h2.ui-search-item__title")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            fraction  = item.select_one("span.andes-money-amount__fraction")
            cents_tag = item.select_one("span.andes-money-amount__cents")
            currency  = item.select_one("span.andes-money-amount__currency-symbol")

            if fraction:
                price_str = fraction.get_text(strip=True).replace(".", "")
                if cents_tag:
                    price_str += f".{cents_tag.get_text(strip=True)}"
                price = float(price_str)
            else:
                price = None

            currency_str = currency.get_text(strip=True) if currency else "R$"

            link_tag = item.select_one("a.ui-search-item__group__element")
            link = link_tag["href"].split("#")[0] if link_tag else "N/A"

            results.append({
                "timestamp": timestamp,
                "mode":      "search",
                "product":   title,
                "price":     price,
                "currency":  currency_str,
                "url":       link,
            })
            logger.info(f"  ✓ {title[:60]}... → {currency_str} {price}")

        except Exception as e:
            logger.warning(f"Erro ao processar item da busca: {e}")
            continue

    return results


# ── Modo 2: Produto específico por URL ────────────────────────────────────────
def fetch_by_url(product_url: str) -> list[dict]:
    """Acessa a página de um produto específico e coleta o preço atual."""
    logger.info(f"[URL] Acessando: {product_url}")

    try:
        response = requests.get(product_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na requisição (URL direta): {e}")
        raise

    soup = BeautifulSoup(response.text, "html.parser")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Título do produto
        title_tag = (
            soup.select_one("h1.ui-pdp-title") or
            soup.select_one("h1.item-title__primary") or
            soup.select_one("h1")
        )
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Preço principal
        fraction  = soup.select_one("span.andes-money-amount__fraction")
        cents_tag = soup.select_one("span.andes-money-amount__cents")
        currency  = soup.select_one("span.andes-money-amount__currency-symbol")

        if fraction:
            price_str = fraction.get_text(strip=True).replace(".", "")
            if cents_tag:
                price_str += f".{cents_tag.get_text(strip=True)}"
            price = float(price_str)
        else:
            price = None
            logger.warning("[URL] Preço não encontrado na página.")

        currency_str = currency.get_text(strip=True) if currency else "R$"

        logger.info(f"  ✓ {title[:60]}... → {currency_str} {price}")

        return [{
            "timestamp": timestamp,
            "mode":      "url",
            "product":   title,
            "price":     price,
            "currency":  currency_str,
            "url":       product_url,
        }]

    except Exception as e:
        logger.error(f"Erro ao extrair dados da página do produto: {e}")
        raise


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

    all_records = []

    # Modo URL direta
    if PRODUCT_URL:
        logger.info(f"Modo: URL direta")
        records = fetch_by_url(PRODUCT_URL)
        all_records.extend(records)

    # Modo busca geral
    if SEARCH_QUERY:
        logger.info(f"Modo: Busca geral | query='{SEARCH_QUERY}' | max={MAX_RESULTS}")
        records = fetch_by_search(SEARCH_QUERY, MAX_RESULTS)
        all_records.extend(records)

    if not PRODUCT_URL and not SEARCH_QUERY:
        logger.error("Nenhuma variável configurada! Defina PRODUCT_URL e/ou SEARCH_QUERY.")
        raise ValueError("PRODUCT_URL e SEARCH_QUERY estão vazios.")

    if all_records:
        save_to_csv(all_records)
    else:
        logger.warning("Nenhum dado coletado.")

    logger.info("Scraper finalizado com sucesso.")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()