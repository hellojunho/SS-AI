FROM ghcr.io/cirruslabs/flutter:stable

WORKDIR /app

RUN flutter config --enable-web

COPY pubspec.yaml /app/pubspec.yaml
RUN flutter pub get

COPY . /app

EXPOSE 9000

CMD ["sh", "-c", "flutter pub get && flutter run -d web-server --web-hostname 0.0.0.0 --web-port 9000 --dart-define=API_BASE_URL=${API_BASE_URL:-http://localhost:9000}"]
