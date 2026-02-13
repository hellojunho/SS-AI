from django.core.management.base import BaseCommand

from app.bootstrap import bootstrap_all


class Command(BaseCommand):
    help = "Apply legacy compatibility patches and bootstrap admin account."

    def handle(self, *args, **options):
        bootstrap_all()
        self.stdout.write(self.style.SUCCESS("Bootstrap completed"))
