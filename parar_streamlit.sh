#!/bin/bash
set -e

APP_PATH="/home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/main.py"

echo "🧹 Matando Streamlit antigo (se existir)..."
pkill -f "streamlit run $APP_PATH" || true

cd /home/cocatis/Projeto_n8n/garimpo_judicial
source venv/bin/activate

cleanup() {
  echo "🛑 Encerrando Streamlit..."
  kill -SIGTERM "$STREAMLIT_PID" 2>/dev/null
  wait "$STREAMLIT_PID" 2>/dev/null
  deactivate
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "🚀 Subindo Streamlit novo..."
streamlit run "$APP_PATH" &
STREAMLIT_PID=$!

wait "$STREAMLIT_PID"

