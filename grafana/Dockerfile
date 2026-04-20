FROM grafana/grafana-oss:13.0.1

USER root

COPY grafana/config.ini ./
RUN cat config.ini >> /etc/grafana/grafana.ini && rm config.ini

USER grafana
