FROM node:20

WORKDIR /app

COPY package*.json ./

# Install build tools
RUN apt-get update && apt-get install -y python3 make g++ \
    && npm install --build-from-source sqlite3

COPY . .

EXPOSE 5656
CMD ["node", "index.js"]
