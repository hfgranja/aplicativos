FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG VITE_IDENTITY_URL=http://localhost:8001
ARG VITE_SCHOOL_URL=http://localhost:8002
ARG VITE_OBSERVATION_URL=http://localhost:8003
ARG VITE_AUDIO_URL=http://localhost:8004
ARG VITE_FEEDBACK_URL=http://localhost:8007
ARG VITE_KNOWLEDGE_URL=http://localhost:8011
ENV VITE_IDENTITY_URL=$VITE_IDENTITY_URL \
    VITE_SCHOOL_URL=$VITE_SCHOOL_URL \
    VITE_OBSERVATION_URL=$VITE_OBSERVATION_URL \
    VITE_AUDIO_URL=$VITE_AUDIO_URL \
    VITE_FEEDBACK_URL=$VITE_FEEDBACK_URL \
    VITE_KNOWLEDGE_URL=$VITE_KNOWLEDGE_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
