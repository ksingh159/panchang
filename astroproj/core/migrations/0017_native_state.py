from django.db import migrations, models


def to_state(apps, schema_editor):
    """Keep an old free-text native place only when it names a state or UT; anything else is cleared."""
    from core.utils.prefs import STATES
    Profile = apps.get_model("core", "UserProfile")
    for p in Profile.objects.exclude(native_state=""):
        text = p.native_state.lower()
        hit = next((s for s in sorted(STATES, key=len, reverse=True) if s.lower() in text), "")
        if hit != p.native_state:
            p.native_state = hit
            p.save(update_fields=["native_state"])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_profile_preferences'),
    ]

    operations = [
        migrations.RenameField(model_name='userprofile', old_name='native_place', new_name='native_state'),
        migrations.RunPython(to_state, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='userprofile', name='native_state',
            field=models.CharField(blank=True, help_text='State or UT the family comes from', max_length=60),
        ),
    ]
