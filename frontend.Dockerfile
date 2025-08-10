FROM node:20-alpine AS build
WORKDIR /app

# Build-time env for Vite
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_BACKEND_URL
ARG VITE_TELEGRAM_BOT_TOKEN
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL:-"https://lipolo.store"} \
    VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY:-"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImV4cCI6MTc4NDQwNjYyOSwiaWF0IjoxNzUyODcwNjI5fQ.WT3UG-bmbfetuQYAYr91n3tvqZAE49YhKJoJZbzxnQc"} \
    VITE_BACKEND_URL=${VITE_BACKEND_URL} \
    VITE_TELEGRAM_BOT_TOKEN=${VITE_TELEGRAM_BOT_TOKEN:-"7774871818:AAHsonb6alqc3QOnjiLrrnyRSUISCvT9OXg"}

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80