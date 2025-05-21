from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ResourceRequest, Department, Resource, UserProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ResourceRequestForm(forms.ModelForm):
    required_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = ResourceRequest
        fields = ['resource', 'required_date', 'duration', 'purpose', 'additional_info']
        widgets = {
            'purpose': forms.Textarea(attrs={'rows': 3}),
            'additional_info': forms.Textarea(attrs={'rows': 3}),
        }
        
class RequestApprovalForm(forms.ModelForm):
    class Meta:
        model = ResourceRequest
        fields = ['status', 'director_notes', 'physical_copy_stamped']
        widgets = {
            'director_notes': forms.Textarea(attrs={'rows': 4}),
        }
        
class ApprovalForm(forms.Form):
    director_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional notes about this request approval or rejection."
    )
    physical_copy_stamped = forms.BooleanField(
        required=False,
        help_text="Check this if a physical copy has been stamped."
    )
        
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'description', 'is_available']  
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['department', 'phone', 'user_type', 'is_director', 'is_admin', 'theme_preference', 'signature_image']
        widgets = {
            'signature_image': forms.ClearableFileInput(attrs={'multiple': False}),
        }

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['department', 'phone', 'user_type', 'is_director', 'is_admin', 'theme_preference']