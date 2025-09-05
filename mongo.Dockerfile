FROM mongo:7.0
COPY init-mongo.js /docker-entrypoint-initdb.d/