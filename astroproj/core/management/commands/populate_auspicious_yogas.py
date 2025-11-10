# management/commands/populate_auspicious_yogas.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.utils import calculate_all_yogas_for_period  # Import from core.utils

class Command(BaseCommand):
    help = 'Populate auspicious yogas database for 60-year period'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--start-year',
            type=int,
            help='Start year for calculation (default: current year - 10)',
        )
        parser.add_argument(
            '--end-year', 
            type=int,
            help='End year for calculation (default: current year + 50)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation and clear existing data',
        )
    
    def handle(self, *args, **options):
        current_year = timezone.now().year
        start_year = options.get('start_year') or (current_year - 10)
        end_year = options.get('end_year') or (current_year + 50)
        
        self.stdout.write(f"Calculating yogas from {start_year} to {end_year}")
        
        if options.get('force'):
            from core.models import AuspiciousYoga
            deleted_count = AuspiciousYoga.objects.filter(
                start_time__year__gte=start_year,
                start_time__year__lte=end_year
            ).delete()[0]
            self.stdout.write(f"Deleted {deleted_count} existing records")
        
        total_yogas = calculate_all_yogas_for_period(start_year, end_year)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {total_yogas} auspicious yogas')
        )