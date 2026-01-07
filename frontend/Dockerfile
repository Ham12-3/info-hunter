FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start development server (with install check)
CMD ["sh", "-c", "npm install && npm run dev"]

