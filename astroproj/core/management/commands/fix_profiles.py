from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create UserProfile for existing users without profiles'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        
        for user in users_without_profiles:
            UserProfile.objects.create(
                user=user,
                city='Varanasi',
                latitude=25.3176,
                longitude=82.9739,
                timezone='Asia/Kolkata'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created profiles for {users_without_profiles.count()} users')
        )