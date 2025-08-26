FROM liquibase:4.33-alpine

WORKDIR /migrations

COPY migrations/migrate.sh ./
COPY migrations/*.yml ./

ENTRYPOINT ["sh", "/migrations/migrate.sh"]

