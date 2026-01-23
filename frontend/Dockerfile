FROM node:20-alpine

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

COPY package.json /app/package.json
RUN npm install

COPY . /app

CMD ["npm", "run", "dev"]
