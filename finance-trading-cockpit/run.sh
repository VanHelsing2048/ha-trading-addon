#!/usr/bin/env sh
set -eu

CONFIG_PATH="/data/options.json"

if [ -f "$CONFIG_PATH" ]; then
  export DATA_MODE="$(python - <<'PY'
import json
with open('/data/options.json', 'r', encoding='utf-8') as f:
    print(json.load(f).get('data_mode', 'demo'))
PY
)"
  export NEWS_RSS_URLS="$(python - <<'PY'
import json
with open('/data/options.json', 'r', encoding='utf-8') as f:
    print(json.load(f).get('news_rss_urls', ''))
PY
)"
fi

export DB_PATH="${DB_PATH:-/config/finance_trading_cockpit.sqlite3}"

uvicorn app.main:app --host 0.0.0.0 --port 8099

