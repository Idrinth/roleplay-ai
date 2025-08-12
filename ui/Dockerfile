FROM node:24-alpine AS build

ARG DESIRED_ROOT=localhost

WORKDIR /build

COPY ui/.minify.json ./
COPY ui/tsconfig.json ./
COPY ui/package.json ./
COPY ui/package-lock.json ./
COPY ui/tools ./tools
COPY ui/public ./public
COPY ui/src ./src
COPY ui/audio ./audio

RUN npm ci && DESIRED_ROOT=${DESIRED_ROOT} npm run build

FROM nginx:alpine

COPY --from=build /build/dist /usr/share/nginx/html

COPY ui/nginx.conf /etc/nginx/conf.d/default.conf
