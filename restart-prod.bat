git pull
docker compose -f compose.beam.yml down
docker compose -f compose.beam.yml up -d --build --remove-orphans
