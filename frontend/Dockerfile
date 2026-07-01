# Multi-stage production Dockerfile for CloudPilot AI Frontend
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage using Nginx
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Default nginx configuration can be copied if custom routing is needed
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
