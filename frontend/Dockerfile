FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache \
    python3 \
    make \
    g++

COPY package.json /app/package.json
RUN npm install

COPY . /app

CMD ["npm", "run", "dev"]
