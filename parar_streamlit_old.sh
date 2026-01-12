#!/bin/bash

echo "🚀 Iniciando streamlit..."

cd /home/cocatis/Projeto_n8n/garimpo_judicial

echo "🚀 Ativando ambiente virtual..."
source venv/bin/activate

streamlit run src/presentation/streamlit_app/main.py


