FROM liquibase:5.0-alpine

WORKDIR /migrations

COPY migrations/migrate.sh ./
COPY migrations/*.yml ./

ENTRYPOINT ["sh", "/migrations/migrate.sh"]

