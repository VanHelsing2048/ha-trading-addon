ARG BUILD_ARCH
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base-python:3.12-alpine3.20

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

SHELL ["/bin/ash", "-o", "pipefail", "-c"]

WORKDIR /app

RUN apk add --no-cache su-exec

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY app ./app
COPY run.sh /run.sh
RUN \
  addgroup -S trading && \
  adduser -S -G trading -h /app trading && \
  chmod a+x /run.sh && \
  chown -R trading:trading /app /run.sh

EXPOSE 8099

CMD ["/run.sh"]
