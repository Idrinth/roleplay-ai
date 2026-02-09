FROM grafana/grafana-oss:12.3.2

USER root

COPY grafana/config.ini ./
RUN cat config.ini >> /etc/grafana/grafana.ini && rm config.ini

USER grafana
