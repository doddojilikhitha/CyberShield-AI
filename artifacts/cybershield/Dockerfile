# Stage 1: Build Vite React SPA
FROM node:20-alpine AS build

WORKDIR /app

# Copy package config and local libraries for installation
COPY lib/api-client-react ./lib/api-client-react
COPY lib/api-zod ./lib/api-zod
COPY artifacts/cybershield/package.json ./artifacts/cybershield/

RUN npm install --prefix artifacts/cybershield

# Copy all code
COPY lib ./lib
COPY artifacts/cybershield ./artifacts/cybershield

RUN npm run build --prefix artifacts/cybershield

# Stage 2: Serve using Nginx
FROM nginx:alpine

COPY --from=build /app/artifacts/cybershield/dist/public /usr/share/nginx/html
# Copy custom nginx configuration to proxy /api calls to the backend
COPY artifacts/cybershield/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
