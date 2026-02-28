#!/bin/bash

echo "🚀 Iniciando streamlit..."

cd /home/cocatis/Projeto_n8n/garimpo_judicial/garimpo_judicial_baseline

echo "🚀 Ativando ambiente virtual..."
source venv_baseline/bin/activate

streamlit run src/presentation/streamlit_app/main.py
              

