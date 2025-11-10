# core/management/commands/cleanup_eclipses.py
from django.core.management.base import BaseCommand
from core.models import Eclipse

class Command(BaseCommand):
    help = 'Clean up eclipse database entries'
    
    def handle(self, *args, **options):
        # Delete invalid eclipses
        invalid_count = Eclipse.objects.filter(date_max__isnull=True).delete()[0]
        
        # Fix lunar eclipse paths
        lunar_eclipses = Eclipse.objects.filter(eclipse_type='lunar')
        for eclipse in lunar_eclipses:
            eclipse.path_geojson = None
            eclipse.central_lat = None
            eclipse.central_lon = None
            eclipse.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up {invalid_count} invalid eclipses and fixed {lunar_eclipses.count()} lunar eclipses'
            )
        )