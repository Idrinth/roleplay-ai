FROM grafana/grafana-oss:12.0.2

USER root

RUN echo "[security]\ndisable_gravatar = true\ncookie_secure = true\ncookie_samesite = strict\ncsrf_trusted_origins = grafana.bjoern-buettner.me\n[users]\nallow_sign_up = false" >> /etc/grafana/grafana.ini

USER grafana