from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from .view_kundali import claim_guest_kundalis
        user_logged_in.connect(claim_guest_kundalis, dispatch_uid="claim_guest_kundalis")
