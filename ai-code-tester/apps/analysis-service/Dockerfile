FROM node:20-alpine AS base
RUN npm install -g pnpm

WORKDIR /app

# Copy workspace manifests
COPY package.json pnpm-workspace.yaml ./
COPY packages/analyzers/package.json ./packages/analyzers/
COPY apps/analysis-service/package.json ./apps/analysis-service/

RUN pnpm install --frozen-lockfile

# Copy source
COPY packages/analyzers/ ./packages/analyzers/
COPY apps/analysis-service/src/ ./apps/analysis-service/src/

WORKDIR /app/apps/analysis-service

ENV NODE_ENV=production PORT=3001
EXPOSE 3001

RUN addgroup -S ait && adduser -S ait -G ait
USER ait

CMD ["node", "src/server.js"]
