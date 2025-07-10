FROM node:24-alpine AS build

RUN npm install minify -g

COPY Ui/public /public
COPY Ui/.minify.json ./
#RUN cat /public/scripts.js | minify --js > /public/scripts.js
RUN cat /public/styles.css | minify --css > /public/styles.css
#RUN cat /public/index.html | minify --html > /public/index.html

FROM nginx:alpine

COPY --from=build /public /usr/share/nginx/html