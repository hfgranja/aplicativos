FROM node:20-alpine AS base
RUN npm install -g pnpm

WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/storage-service/package.json ./apps/storage-service/

RUN pnpm install --frozen-lockfile

COPY apps/storage-service/src/ ./apps/storage-service/src/

WORKDIR /app/apps/storage-service

ENV NODE_ENV=production PORT=3004 CLOUD_PROVIDER=local
EXPOSE 3004

RUN addgroup -S ait && adduser -S ait -G ait
USER ait

CMD ["node", "src/server.js"]
