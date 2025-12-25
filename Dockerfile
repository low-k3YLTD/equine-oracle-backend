FROM node:18-slim

# System deps for lightgbm/xgboost wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip gcc g++ libomp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps with bypass flag (safe in container)
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt; \
    fi

# Node deps
COPY package*.json ./
RUN npm ci --omit=dev

# Copy code
COPY . .

CMD ["npm", "start"]
