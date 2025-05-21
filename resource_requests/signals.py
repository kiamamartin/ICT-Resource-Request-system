from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for new users"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    instance.profile.save()

@receiver(post_save, sender=UserProfile)
def assign_user_groups(sender, instance, **kwargs):
    """Assign users to appropriate groups based on their user_type"""
    # Make sure the groups exist
    ict_director_group, _ = Group.objects.get_or_create(name='ICTDirector')
    department_user_group, _ = Group.objects.get_or_create(name='DepartmentUser')
    
    user = instance.user
    
    # Remove from all groups first to avoid duplicates
    user.groups.clear()
    
    # Assign to appropriate group based on user_type
    if instance.user_type == 'director' or instance.is_director:
        user.groups.add(ict_director_group)
    else:
        user.groups.add(department_user_group)