"""python manage.py vapid_keys - make the key pair for the morning notification (Web Push).

Run once. Put the two printed lines into Railway's variables (web service and the cron service). Do not commit
them and do not run this again later: a new pair cuts off every browser that already subscribed.
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class Command(BaseCommand):
    help = "Print a new VAPID key pair for Web Push (run once, store in Railway variables)."

    def handle(self, *args, **options):
        key = ec.generate_private_key(ec.SECP256R1())
        private = _b64(key.private_numbers().private_value.to_bytes(32, "big"))
        public = _b64(key.public_key().public_bytes(serialization.Encoding.X962,
                                                    serialization.PublicFormat.UncompressedPoint))
        self.stdout.write(f"VAPID_PUBLIC_KEY={public}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private}")
