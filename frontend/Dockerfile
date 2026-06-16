# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies with legacy-peer-deps due to react-simple-maps
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Define build arguments
ARG VITE_API_URL
ARG VITE_WS_URL

# Set environment variables for the build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Build the application
RUN npm run build

# Production server stage
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
