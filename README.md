# 🕷️ ML Price Tracker

Rastreador automático de preços do Mercado Livre com histórico em CSV e monitoramento de erros via GitHub Actions.

## 📁 Estrutura

```
.
├── scraper.py               # Script principal
├── requirements.txt         # Dependências Python
├── data/
│   └── prices.csv           # Histórico de preços (gerado automaticamente)
├── logs/
│   └── scraper.log          # Logs de execução (gerado automaticamente)
└── .github/
    └── workflows/
        └── scraper.yml      # Pipeline CI/CD (roda todo dia ao meio-dia UTC)
```

## 🚀 Como usar

### 1. Clone e configure o repositório

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPO.git
cd SEU_REPO
```

### 2. Configure as variáveis no GitHub

Vá em **Settings → Variables → Actions** e adicione:

| Variável       | Descrição                          | Exemplo       |
|----------------|------------------------------------|---------------|
| `SEARCH_QUERY` | Produto a buscar no ML             | `iphone 15`   |
| `MAX_RESULTS`  | Quantos produtos registrar por dia | `10`          |

### 3. Ative o workflow

- Vá em **Actions** no seu repositório
- Clique em **ML Price Scraper**
- Clique em **Run workflow** para testar manualmente

A partir daí ele roda automaticamente todo dia ao meio-dia (UTC) — equivalente a 9h no horário de Brasília.

## 💻 Rodar localmente

```bash
pip install -r requirements.txt

# Opcional: defina variáveis de ambiente
export SEARCH_QUERY="iphone 15"
export MAX_RESULTS=10

python scraper.py
```

## 📊 Formato do CSV

```
timestamp,product,price,currency,url
2024-01-15 12:00:00,iPhone 15 128GB,4599.99,R$,https://...
```

## 🔍 Monitoramento de erros

- **Logs locais**: `logs/scraper.log`
- **Artefatos no GitHub**: cada execução do Actions salva o log por 7 dias
- **Job com falha**: se o scraper lançar exceção, o Actions marca o job como ❌ e você recebe email de notificação

## ⚠️ Observações

- O seletor CSS do ML pode mudar com o tempo. Se parar de coletar dados, verifique os seletores em `scraper.py`.
- Use com moderação para não sobrecarregar os servidores do ML.

