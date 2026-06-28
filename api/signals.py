import sys
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, UserSettings

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created and 'test' not in sys.argv:
        # Create default UserSettings
        UserSettings.objects.get_or_create(user=instance)

        defaults = [
            {'name': 'Food', 'icon': 'ph-hamburger', 'color': '#10b981'},
            {'name': 'Travel', 'icon': 'ph-car', 'color': '#06b6d4'},
            {'name': 'Other', 'icon': 'ph-package', 'color': '#6b7280'},
        ]
        for cat in defaults:
            Category.objects.get_or_create(
                user=instance,
                name=cat['name'],
                defaults={
                    'icon': cat['icon'],
                    'color': cat['color'],
                }
            )

