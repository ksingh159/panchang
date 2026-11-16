from django.core.management.base import BaseCommand

from core.utils import payments
from core.utils.pdf_store import purge_expired


class Command(BaseCommand):
    help = "Delete saved order PDFs whose download window has closed. Run daily from cron."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only report what would be deleted")
        parser.add_argument("--grace-days", type=int, default=2)

    def handle(self, *args, dry_run=False, grace_days=2, **opts):
        files, size = purge_expired(payments.DOWNLOAD_DAYS, grace_days=grace_days, dry_run=dry_run)
        verb = "Would delete" if dry_run else "Deleted"
        self.stdout.write(f"{verb} {files} PDF(s), {size / 1_048_576:.1f} MB")
