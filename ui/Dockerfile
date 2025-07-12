FROM node:24-alpine AS build

RUN npm install minify -g

COPY ui/.minify.json ./
COPY ui/public /public

RUN cat /public/scripts.js | minify --js > /tmp/scripts.js && \
    [ -s /tmp/scripts.js ] && cp /tmp/scripts.js /public/scripts.js || echo "JS minification failed, keeping original"

RUN cat /public/styles.css | minify --css > /tmp/styles.css && \
    [ -s /tmp/styles.css ] && cp /tmp/styles.css /public/styles.css || echo "CSS minification failed, keeping original"

RUN cat /public/index.html | minify --html > /tmp/index.html && \
    [ -s /tmp/index.html ] && cp /tmp/index.html /public/index.html || echo "HTML minification failed, keeping original"

FROM nginx:alpine

COPY --from=build /public /usr/share/nginx/html
