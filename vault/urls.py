from django.urls import path
from . import views

urlpatterns = [
    path('', views.viewer_login, name='home'),
    path('upload/', views.upload_document, name='upload'),
    path('download/<int:document_id>/', views.download_document, name='download'),
    path('login/', views.viewer_login, name='viewer_login'),
    path('documents/', views.document_list, name='document_list'),
    path('search/', views.search_documents, name='search_documents'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('edit/<int:document_id>/', views.edit_document, name='edit_document'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('permissions/', views.manage_permissions, name='manage_permissions'),
    path('verify-audit/', views.verify_audit_logs, name='verify_audit'),
    path('fix-audit-hashes-2026/', views.fix_render_audit_hashes, name='fix_audit_hashes'),
]