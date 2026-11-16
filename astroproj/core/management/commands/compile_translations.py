"""Build locale/*/LC_MESSAGES/django.mo from django.po without needing GNU gettext installed."""
import ast
import struct

from django.conf import settings
from django.core.management.base import BaseCommand


def read_po(path):
    pairs, msgid, field = {}, None, None
    for line in open(path, encoding="utf8"):
        line = line.strip()
        if line.startswith("msgid "):
            msgid, field = ast.literal_eval(line[6:]), "id"
        elif line.startswith("msgstr "):
            pairs[msgid], field = ast.literal_eval(line[7:]), "str"
        elif line.startswith('"'):
            piece = ast.literal_eval(line)
            if field == "id":
                msgid += piece
            elif field == "str":
                pairs[msgid] += piece
    return pairs


def write_mo(pairs, path):
    pairs = sorted((k.encode("utf8"), v.encode("utf8")) for k, v in pairs.items() if v)
    count = len(pairs)
    id_table, str_table = 28, 28 + count * 8
    cursor = 28 + count * 16
    ids, strs, blob = [], [], b""
    for k, _ in pairs:
        ids.append((len(k), cursor + len(blob)))
        blob += k + b"\0"
    for _, v in pairs:
        strs.append((len(v), cursor + len(blob)))
        blob += v + b"\0"
    with open(path, "wb") as f:
        f.write(struct.pack("<7I", 0x950412DE, 0, count, id_table, str_table, 0, cursor))
        for row in ids + strs:
            f.write(struct.pack("<2I", *row))
        f.write(blob)


class Command(BaseCommand):
    help = "Compile the Hindi catalogue"

    def handle(self, *args, **options):
        for root in settings.LOCALE_PATHS:
            for po in root.glob("*/LC_MESSAGES/django.po"):
                pairs = read_po(po)
                write_mo(pairs, po.with_suffix(".mo"))
                self.stdout.write(f"{po}: {len(pairs) - 1} strings")
