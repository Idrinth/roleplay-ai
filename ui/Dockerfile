FROM node:24-alpine AS build

RUN npm install minify -g

WORKDIR /build

COPY ui/.minify.json ./
COPY ui/package.json ./
COPY ui/package-lock.json ./
COPY ui/tools ./tools
COPY ui/public /public

RUN npm ci && npm run build

FROM nginx:alpine

COPY --from=build /build/dist /usr/share/nginx/html

COPY ui/nginx.conf /etc/nginx/conf.d/default.conf
