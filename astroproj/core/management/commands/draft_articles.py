from django.core.management.base import BaseCommand

from core.utils.articles import draft_upcoming


class Command(BaseCommand):
    help = ("Draft blog articles for the major festivals coming up, from the site's own calculations. "
            "Drafts stay hidden until published in the admin. Run weekly from cron.")

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=45)

    def handle(self, *args, **opts):
        made = draft_upcoming(days=opts["days"])
        for a in made:
            self.stdout.write(f"draft: {a.title}")
        self.stdout.write(self.style.SUCCESS(f"{len(made)} new draft(s). Review them in the admin under Articles."))
