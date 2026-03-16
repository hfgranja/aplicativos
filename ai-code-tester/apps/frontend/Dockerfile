FROM node:20-alpine AS dev
RUN npm install -g pnpm
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/frontend/package.json ./apps/frontend/
RUN pnpm install
COPY apps/frontend/ ./apps/frontend/
WORKDIR /app/apps/frontend
EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

FROM node:20-alpine AS builder
RUN npm install -g pnpm
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
COPY apps/frontend/package.json ./apps/frontend/
RUN pnpm install --frozen-lockfile
COPY apps/frontend/ ./apps/frontend/
WORKDIR /app/apps/frontend
RUN pnpm build

FROM nginx:1.27-alpine AS production
COPY --from=builder /app/apps/frontend/dist /usr/share/nginx/html
COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
