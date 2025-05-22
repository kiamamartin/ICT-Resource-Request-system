from django.core.management.base import BaseCommand
from django.utils import timezone
from resource_requests.models import UserProfile

class Command(BaseCommand):
    help = 'Checks for expired delegations and resets approval rights'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find all deputy directors with delegated approval rights that have expired
        expired_delegations = UserProfile.objects.filter(
            is_deputy_director=True,
            has_approval_rights=True,
            approval_rights_delegation_end__lt=now
        )
        
        for deputy in expired_delegations:
            # Get the director who delegated the rights
            director = deputy.approval_rights_delegated_by
            
            if director:
                # Reset the deputy's approval rights
                deputy.has_approval_rights = False
                deputy.approval_rights_delegated_at = None
                deputy.approval_rights_delegation_end = None
                deputy.approval_rights_delegated_by = None
                deputy.save()
                
                # Restore the director's approval rights
                director.has_approval_rights = True
                director.save()
                
                # Update the delegation log
                from resource_requests.models import DelegationLog
                try:
                    log = DelegationLog.objects.filter(
                        delegated_by=director.user,
                        delegated_to=deputy.user,
                        actual_end_date__isnull=True
                    ).latest('created_at')
                    
                    log.actual_end_date = now
                    log.save()
                except DelegationLog.DoesNotExist:
                    pass
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully expired delegation from {director.user.username} to {deputy.user.username}'
                ))
        
        if not expired_delegations:
            self.stdout.write(self.style.SUCCESS('No expired delegations found'))