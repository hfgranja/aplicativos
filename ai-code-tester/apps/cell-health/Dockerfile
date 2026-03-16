FROM node:20-alpine AS base
RUN npm install -g pnpm

WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/cell-health/package.json ./apps/cell-health/

RUN pnpm install --frozen-lockfile

COPY apps/cell-health/src/ ./apps/cell-health/src/

WORKDIR /app/apps/cell-health

ENV NODE_ENV=production PORT=3005 CELL_ID=local
EXPOSE 3005

RUN addgroup -S ait && adduser -S ait -G ait
USER ait

CMD ["node", "src/server.js"]
