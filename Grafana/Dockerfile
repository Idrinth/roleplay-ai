FROM grafana/grafana-oss:12.0.2

USER root

COPY Grafana/config.ini ./
RUN cat config.ini >> /etc/grafana/grafana.ini && rm config.ini

USER grafana