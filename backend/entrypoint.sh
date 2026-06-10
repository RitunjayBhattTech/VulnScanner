#!/bin/bash
set -e

# Wait for Postgres to be ready
echo "Waiting for database to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
  sleep 1
done
echo "Database is ready!"

# Pull Ollama model if needed (only for backend service, not worker)
if [ "$SERVICE_TYPE" = "api" ]; then
  echo "Checking Ollama models..."
  OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://ollama:11434/api/tags || echo "000")
  if [ "$OLLAMA_STATUS" = "200" ]; then
    echo "Ollama is running. Pulling mistral:7b..."
    curl -X POST http://ollama:11434/api/pull -d '{"name":"mistral:7b"}' || echo "Model may already exist"
    sleep 5
  else
    echo "Ollama not ready yet, will try again later"
  fi
fi

exec "$@"