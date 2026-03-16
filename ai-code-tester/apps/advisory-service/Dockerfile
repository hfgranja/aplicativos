FROM node:20-alpine AS base
RUN npm install -g pnpm

WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/advisory-service/package.json ./apps/advisory-service/

RUN pnpm install --frozen-lockfile

COPY apps/advisory-service/src/ ./apps/advisory-service/src/

WORKDIR /app/apps/advisory-service

ENV NODE_ENV=production PORT=3002 \
    OLLAMA_URL=http://localhost:11434 \
    DEVSTRAL_MODEL=devstral \
    QWEN_MODEL=qwen3-coder

EXPOSE 3002

RUN addgroup -S ait && adduser -S ait -G ait
USER ait

CMD ["node", "src/server.js"]
