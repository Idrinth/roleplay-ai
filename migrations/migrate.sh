liquibase changeLogSync --url="jdbc:mariadb://mariadb:3306/chat_users" --changeLogFile=sql-migrations.yml --username=root --password=example
liquibase update --url="jdbc:mariadb://mariadb:3306/chat_users" --changeLogFile=sql-migrations.yml --username=root --password=example
