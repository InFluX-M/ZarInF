FROM docker.arvancloud.ir/node:20

WORKDIR /app

# Update npm
RUN npm install -g npm@11.4.1

# Copy and install deps
COPY package.json package-lock.json ./
RUN npm ci --verbose

# Copy rest of app
COPY . .

EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--host"]
