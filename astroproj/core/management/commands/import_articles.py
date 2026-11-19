"""Load articles/*.md into the Article table (run by `release` on every deploy)."""
from django.conf import settings
from django.core.management.base import BaseCommand

from core.utils.articles import ARTICLES_DIR_NAME, import_article_files


class Command(BaseCommand):
    help = "Create or update an Article for every Markdown file in articles/; publish those whose publish_date has come."

    def handle(self, *args, **options):
        for a in import_article_files(settings.BASE_DIR / ARTICLES_DIR_NAME):
            self.stdout.write(f"{a.status:9} /blog/{a.slug}/  FAQ: {len(a.faq)}  muhurat links: {', '.join(a.muhurat_purposes) or '-'}")
