# Makefile for SS-AI project

.PHONY: init reset

# Start everything, recreating containers and ensuring admin account is created on startup

init:
	docker compose down
	# Run in foreground so logs remain in this console
	docker compose up --build

# Reset DB (remove volumes) and restart services. Admin account will be recreated on backend startup.
reset:
	docker compose down -v
	# Run in foreground so logs remain in this console
	docker compose up --build


update:
	docker compose down
	git pull origin main
	docker compose up --build


mobile-update:
	docker compose down
	git pull
	# Start only the mobile service (rebuild it) and run in background
	docker compose up -d --build mobile
	@echo "Mobile service rebuilt and started (background)."
	@echo "To update Flutter deps locally: cd mobile && flutter pub get"

superuser:
	# Create a superuser for the backend-drf (Django)
	docker compose exec backend-drf python manage.py createsuperuser