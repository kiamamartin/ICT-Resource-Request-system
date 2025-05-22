from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('requests/new/', views.new_request, name='new_request'),
    path('requests/my/', views.my_requests, name='my_requests'),
    path('requests/pending/', views.pending_requests, name='pending_requests'),
    path('requests/<str:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<str:request_id>/approve/', views.approve_request, name='approve_request'),
    path('departments/', views.departments, name='departments'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<int:department_id>/edit/', views.edit_department, name='edit_department'),
    path('departments/<int:department_id>/delete/', views.delete_department, name='delete_department'),
    path('resources/', views.resources, name='resources'),
    path('resources/add/', views.add_resource, name='add_resource'),
    path('resources/<int:resource_id>/edit/', views.edit_resource, name='edit_resource'),
    path('resources/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    path('users/', views.users, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('profile/', views.profile, name='profile'),
    path('ledger/', views.ledger, name='ledger'),
    path('save-theme-preference/', views.save_theme_preference, name='save_theme_preference'),
    path('delegate-approval-rights/', views.delegate_approval_rights, name='delegate_approval_rights'),
    path('reclaim-approval-rights/', views.reclaim_approval_rights, name='reclaim_approval_rights'),
]