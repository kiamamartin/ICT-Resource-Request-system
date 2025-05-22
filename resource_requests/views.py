from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.utils import timezone
from .models import ResourceRequest, Department, Resource, Ledger, UserProfile
from .forms import (
    ResourceRequestForm, ApprovalForm, DepartmentForm, ResourceForm, 
    UserRegisterForm, UserProfileForm, UserForm, ProfileForm, DelegateApprovalRightsForm
)
import datetime
import uuid
import base64

def is_ict_director(user):
    """Check if user is in ICTDirector group or is a superuser"""
    return user.is_superuser or user.groups.filter(name='ICTDirector').exists()

def is_department_user(user):
    """Check if user is in DepartmentUser group"""
    return user.groups.filter(name='DepartmentUser').exists()

@login_required
def dashboard(request):
    # Get counts for the dashboard
    my_requests_count = ResourceRequest.objects.filter(requestor=request.user).count()
    pending_count = ResourceRequest.objects.filter(requestor=request.user, status='pending').count()
    approved_count = ResourceRequest.objects.filter(requestor=request.user, status='approved').count()
    rejected_count = ResourceRequest.objects.filter(requestor=request.user, status='rejected').count()
    
    # Get recent requests
    recent_requests = ResourceRequest.objects.filter(requestor=request.user).order_by('-submitted_at')[:5]
    
    # Get pending approvals for directors and admins
    pending_approvals = []
    if is_ict_director(request.user):
        # ICT Directors see all pending requests
        pending_approvals = ResourceRequest.objects.filter(
            status='pending'
        ).order_by('-submitted_at')[:5]
    
    context = {
        'my_requests_count': my_requests_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'recent_requests': recent_requests,
        'pending_approvals': pending_approvals,
        'is_ict_director': is_ict_director(request.user)
    }
    
    return render(request, 'resource_requests/dashboard.html', context)

@login_required
def my_requests(request):
    status_filter = request.GET.get('status', '')
    
    if status_filter and status_filter in ['pending', 'approved', 'rejected', 'completed']:
        requests = ResourceRequest.objects.filter(requestor=request.user, status=status_filter).order_by('-submitted_at')
    else:
        requests = ResourceRequest.objects.filter(requestor=request.user).order_by('-submitted_at')
    
    paginator = Paginator(requests, 10)  # Show 10 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'resource_requests/my_requests.html', context)

@login_required
def new_request(request):
    # Only department users can create new requests
    if not is_department_user(request.user) and not request.user.is_superuser:
        messages.error(request, "You don't have permission to create requests.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = ResourceRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.requestor = request.user
            request_obj.department = request.user.profile.department
            request_obj.status = 'pending'
            
            # Generate a unique request ID
            today = datetime.date.today()
            prefix = f"REQ-{today.strftime('%Y%m%d')}"
            random_suffix = uuid.uuid4().hex[:6].upper()
            request_obj.request_id = f"{prefix}-{random_suffix}"
            
            request_obj.save()
            messages.success(request, 'Your request has been submitted successfully.')
            return redirect('dashboard')
    else:
        form = ResourceRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'resource_requests/new_request.html', context)

@login_required
def request_detail(request, request_id):
    request_obj = get_object_or_404(ResourceRequest, request_id=request_id)
    
    # Check if user has permission to view this request
    if not (request.user == request_obj.requestor or is_ict_director(request.user)):
        messages.error(request, "You don't have permission to view this request.")
        return redirect('dashboard')
    
    # Get ledger entry if request is approved
    ledger_entry = None
    if request_obj.status == 'approved':
        try:
            ledger_entry = Ledger.objects.get(request=request_obj)
        except Ledger.DoesNotExist:
            pass
    
    context = {
        'request': request_obj,
        'ledger_entry': ledger_entry,
    }
    
    return render(request, 'resource_requests/request_detail.html', context)

@login_required
def pending_requests(request):
    # Check if user has permission to view pending requests
    # Updated to check for has_approval_rights
    if not ((request.user.profile.is_director or request.user.profile.is_deputy_director) and 
            request.user.profile.has_approval_rights or 
            request.user.profile.is_admin or 
            request.user.is_staff):
        messages.error(request, "You don't have permission to view pending requests.")
        return redirect('dashboard')
    
    if (request.user.profile.is_director or request.user.profile.is_deputy_director) and request.user.profile.has_approval_rights:
        # Directors or deputies with approval rights only see requests from their department
        pending = ResourceRequest.objects.filter(
            department=request.user.profile.department,
            status='pending'
        ).order_by('-submitted_at')
    else:
        # Admins see all pending requests
        pending = ResourceRequest.objects.filter(status='pending').order_by('-submitted_at')
    
    paginator = Paginator(pending, 10)  # Show 10 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'resource_requests/pending_requests.html', context)

@login_required
def approve_request(request, request_id):
    request_obj = get_object_or_404(ResourceRequest, request_id=request_id)
    
    # Check if user has permission to approve requests
    # Updated to check for has_approval_rights instead of just is_director
    if not ((request.user.profile.is_director or request.user.profile.is_deputy_director) and 
            request.user.profile.has_approval_rights or 
            request.user.profile.is_admin or 
            request.user.is_staff):
        messages.error(request, "You don't have permission to approve requests.")
        return redirect('dashboard')
    
    # Directors can only approve requests from their department
    if (request.user.profile.is_director or request.user.profile.is_deputy_director) and request.user.profile.department != request_obj.department:
        messages.error(request, "You can only approve requests from your department.")
        return redirect('pending_requests')
    
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            status = request.POST.get('status')
            request_obj.status = status
            request_obj.director_notes = form.cleaned_data['director_notes']
            request_obj.physical_copy_stamped = form.cleaned_data.get('physical_copy_stamped', False)
            request_obj.approved_by = request.user
            request_obj.approved_at = timezone.now()
            
            # Handle signature data
            signature_data = request.POST.get('signature_data')
            if signature_data and signature_data.startswith('data:image/png;base64,'):
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr))
                file_name = f"signature_{request_obj.request_id}.{ext}"
                request_obj.signature_image.save(file_name, data, save=False)
                request_obj.stamp_date = timezone.now()
            
            request_obj.save()
            
            # Create ledger entry if approved
            if status == 'approved':
                ledger = Ledger()
                ledger.request = request_obj
                ledger.resource = request_obj.resource
                ledger.department = request_obj.department
                ledger.requestor = request_obj.requestor
                ledger.approved_by = request.user
                
                # Generate a unique ledger ID
                today = datetime.date.today()
                prefix = f"LDG-{today.strftime('%Y%m%d')}"
                random_suffix = uuid.uuid4().hex[:6].upper()
                ledger.ledger_id = f"{prefix}-{random_suffix}"
                
                ledger.save()
                
                messages.success(request, f"Request {request_obj.request_id} has been approved.")
            else:
                messages.success(request, f"Request {request_obj.request_id} has been rejected.")
            
            return redirect('pending_requests')
    else:
        form = ApprovalForm()
    
    context = {
        'form': form,
        'request': request_obj,
    }
    
    return render(request, 'resource_requests/approve_request.html', context)


@login_required
def departments(request):
    # Check if user has permission to view departments
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to view departments.")
        return redirect('dashboard')
    
    departments_list = Department.objects.all().order_by('name')
    
    context = {
        'departments': departments_list,
    }
    
    return render(request, 'resource_requests/departments.html', context)

@login_required
def add_department(request):
    # Check if user has permission to add departments
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to add departments.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added successfully.")
            return redirect('departments')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'action': 'Add',
    }
    
    return render(request, 'resource_requests/department_form.html', context)

@login_required
def edit_department(request, department_id):
    # Check if user has permission to edit departments
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to edit departments.")
        return redirect('dashboard')
    
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
            return redirect('departments')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'action': 'Edit',
    }
    
    return render(request, 'resource_requests/department_form.html', context)

@login_required
def delete_department(request, department_id):
    # Check if user has permission to delete departments
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to delete departments.")
        return redirect('dashboard')
    
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        # Check if department has any requests
        if ResourceRequest.objects.filter(department=department).exists():
            messages.error(request, "Cannot delete department with existing requests.")
            return redirect('departments')
        
        # Check if department has any users
        if UserProfile.objects.filter(department=department).exists():
            messages.error(request, "Cannot delete department with assigned users.")
            return redirect('departments')
        
        department.delete()
        messages.success(request, "Department deleted successfully.")
        return redirect('departments')
    
    context = {
        'department': department,
    }
    
    return render(request, 'resource_requests/delete_department.html', context)

@login_required
def resources(request):
    # Check if user has permission to view resources
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to view resources.")
        return redirect('dashboard')
    
    resources_list = Resource.objects.all().order_by('name')
    
    context = {
        'resources': resources_list,
    }
    
    return render(request, 'resource_requests/resources.html', context)

@login_required
def add_resource(request):
    # Check if user has permission to add resources
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to add resources.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource added successfully.")
            return redirect('resources')
    else:
        form = ResourceForm()
    
    context = {
        'form': form,
        'action': 'Add',
    }
    
    return render(request, 'resource_requests/resource_form.html', context)

@login_required
def edit_resource(request, resource_id):
    # Check if user has permission to edit resources
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to edit resources.")
        return redirect('dashboard')
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated successfully.")
            return redirect('resources')
    else:
        form = ResourceForm(instance=resource)
    
    context = {
        'form': form,
        'action': 'Edit',
    }
    
    return render(request, 'resource_requests/resource_form.html', context)

@login_required
def delete_resource(request, resource_id):
    # Check if user has permission to delete resources
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to delete resources.")
        return redirect('dashboard')
    
    resource = get_object_or_404(Resource, id=resource_id)
    
    if request.method == 'POST':
        # Check if resource has any requests
        if ResourceRequest.objects.filter(resource=resource).exists():
            messages.error(request, "Cannot delete resource with existing requests.")
            return redirect('resources')
        
        resource.delete()
        messages.success(request, "Resource deleted successfully.")
        return redirect('resources')
    
    context = {
        'resource': resource,
    }
    
    return render(request, 'resource_requests/delete_resource.html', context)

@login_required
def users(request):
    # Check if user has permission to view users
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to view users.")
        return redirect('dashboard')
    
    users_list = User.objects.all().order_by('username')
    
    context = {
        'users': users_list,
    }
    
    return render(request, 'resource_requests/users.html', context)

@login_required
def add_user(request):
    # Check if user has permission to add users
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to add users.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, "User added successfully.")
            return redirect('users')
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'action': 'Add',
    }
    
    return render(request, 'resource_requests/user_form.html', context)

@login_required
def edit_user(request, user_id):
    # Check if user has permission to edit users
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to edit users.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=user)
        profile.save()
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            messages.success(request, "User updated successfully.")
            return redirect('users')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'action': 'Edit',
    }
    
    return render(request, 'resource_requests/user_form.html', context)

@login_required
def delete_user(request, user_id):
    # Check if user has permission to delete users
    if not (request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to delete users.")
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('users')
    
    if request.method == 'POST':
        # Check if user has any requests
        if ResourceRequest.objects.filter(requestor=user).exists():
            messages.error(request, "Cannot delete user with existing requests.")
            return redirect('users')
        
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect('users')
    
    context = {
        'user': user,
    }
    
    return render(request, 'resource_requests/delete_user.html', context)

@login_required
def profile(request):
    user = request.user
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=user)
        profile.save()
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'resource_requests/profile.html', context)

@login_required
def ledger(request):
    # Check if user has permission to view ledger
    if not is_ict_director(request.user):
        messages.error(request, "You don't have permission to view the ledger.")
        return redirect('dashboard')
    
    # ICT Directors see all ledger entries
    ledger_entries = Ledger.objects.all().order_by('-created_at')
    
    paginator = Paginator(ledger_entries, 10)  # Show 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'resource_requests/ledger.html', context)

@login_required
def save_theme_preference(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=request.user)
        
        profile.theme_preference = theme
        profile.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delegate_approval_rights(request):
    # Check if user is a director with approval rights
    if not (request.user.profile.is_director and request.user.profile.has_approval_rights):
        messages.error(request, "You don't have permission to delegate approval rights.")
        return redirect('dashboard')
    
    # Get all deputy directors
    deputy_directors = UserProfile.objects.filter(is_deputy_director=True)
    
    if request.method == 'POST':
        form = DelegateApprovalRightsForm(request.POST)
        form.fields['delegate_to'].queryset = deputy_directors
        
        if form.is_valid():
            delegate_to = form.cleaned_data['delegate_to']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            reason = form.cleaned_data['reason']
            
            # Remove approval rights from director
            director_profile = request.user.profile
            director_profile.has_approval_rights = False
            director_profile.save()
            
            # Grant approval rights to deputy
            delegate_to.has_approval_rights = True
            delegate_to.approval_rights_delegated_at = start_date
            delegate_to.approval_rights_delegation_end = end_date
            delegate_to.approval_rights_delegated_by = director_profile
            delegate_to.save()
            
            # Create a log entry for the delegation
            DelegationLog.objects.create(
                delegated_by=request.user,
                delegated_to=delegate_to.user,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )
            
            # Send notification to deputy director
            # (You can implement this using Django signals or a notification system)
            
            messages.success(request, f"Approval rights successfully delegated to {delegate_to.user.get_full_name()}.")
            return redirect('dashboard')
    else:
        form = DelegateApprovalRightsForm()
        form.fields['delegate_to'].queryset = deputy_directors
    
    context = {
        'form': form,
    }
    
    return render(request, 'resource_requests/delegate_approval_rights.html', context)

@login_required
def reclaim_approval_rights(request):
    # Check if user is a director without approval rights
    if not (request.user.profile.is_director and not request.user.profile.has_approval_rights):
        messages.error(request, "You don't have permission to reclaim approval rights.")
        return redirect('dashboard')
    
    # Find the deputy who currently has approval rights
    try:
        deputy = UserProfile.objects.get(
            is_deputy_director=True,
            has_approval_rights=True,
            approval_rights_delegated_by=request.user.profile
        )
    except UserProfile.DoesNotExist:
        messages.error(request, "No active delegation found.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Remove approval rights from deputy
        deputy.has_approval_rights = False
        deputy.approval_rights_delegated_at = None
        deputy.approval_rights_delegation_end = None
        deputy.approval_rights_delegated_by = None
        deputy.save()
        
        # Restore approval rights to director
        director_profile = request.user.profile
        director_profile.has_approval_rights = True
        director_profile.save()
        
        # Update the delegation log
        try:
            log = DelegationLog.objects.filter(
                delegated_by=request.user,
                delegated_to=deputy.user,
                actual_end_date__isnull=True
            ).latest('created_at')
            
            log.actual_end_date = timezone.now()
            log.save()
        except DelegationLog.DoesNotExist:
            pass
        
        messages.success(request, "Approval rights have been reclaimed successfully.")
        return redirect('dashboard')
    
    context = {
        'deputy': deputy,
    }
    
    return render(request, 'resource_requests/reclaim_approval_rights.html', context)

@login_required
def delegation_history(request):
    # Check if user has permission to view delegation history
    if not (request.user.profile.is_director or request.user.profile.is_deputy_director or 
            request.user.profile.is_admin or request.user.is_staff):
        messages.error(request, "You don't have permission to view delegation history.")
        return redirect('dashboard')
    
    # Get delegation logs
    if request.user.profile.is_director:
        # Directors see their own delegations
        logs = DelegationLog.objects.filter(delegated_by=request.user).order_by('-created_at')
    elif request.user.profile.is_deputy_director:
        # Deputy directors see delegations to them
        logs = DelegationLog.objects.filter(delegated_to=request.user).order_by('-created_at')
    else:
        # Admins see all delegations
        logs = DelegationLog.objects.all().order_by('-created_at')
    
    paginator = Paginator(logs, 10)  # Show 10 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'resource_requests/delegation_history.html', context)