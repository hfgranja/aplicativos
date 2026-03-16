FROM node:20-alpine AS base
RUN npm install -g pnpm

WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/git-proxy/package.json ./apps/git-proxy/

RUN pnpm install --frozen-lockfile

COPY apps/git-proxy/src/ ./apps/git-proxy/src/

WORKDIR /app/apps/git-proxy

ENV NODE_ENV=production PORT=3003
EXPOSE 3003

RUN addgroup -S ait && adduser -S ait -G ait
USER ait

CMD ["node", "src/server.js"]
