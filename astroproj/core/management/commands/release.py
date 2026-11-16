"""Run on every deploy, before the new version takes traffic (Railway preDeployCommand)."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deploy step: migrate the database, create the cache table, compile the Hindi translations."

    def handle(self, *args, **options):
        call_command("migrate", interactive=False)
        call_command("createcachetable")
        call_command("compile_translations")
