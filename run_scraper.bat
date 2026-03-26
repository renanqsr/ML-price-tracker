@echo off
:: ─────────────────────────────────────────────────────────────
:: ML Price Tracker - Executar scraper e commitar no GitHub
:: ─────────────────────────────────────────────────────────────

:: ✏️ EDITE AQUI o caminho da sua pasta do projeto
set REPO_DIR=C:\Users\wesle\Documents\GitHub\ML-price-tracker

:: ✏️ EDITE AQUI o caminho do seu Python (rode "where python" no terminal pra descobrir)
set PYTHON=python

:: ─────────────────────────────────────────────────────────────
cd /d "%REPO_DIR%"

echo [%date% %time%] Iniciando scraper...
%PYTHON% scraper.py

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] ERRO: scraper falhou com codigo %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Fazendo commit no GitHub...
git add data/prices.csv logs/scraper.log
git diff --cached --quiet && (
    echo [%date% %time%] Nenhuma mudanca para commitar.
) || (
    git commit -m "chore(data): precos coletados em %date% %time%"
    git push
    echo [%date% %time%] Commit e push realizados com sucesso!
)

echo [%date% %time%] Concluido!