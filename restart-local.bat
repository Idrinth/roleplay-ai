git pull
docker compose -f compose.local.yml down
docker compose -f compose.local.yml up -d --build --remove-orphans
