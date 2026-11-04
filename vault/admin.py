
from django.contrib import admin
from .models import Profile, Document, DocumentPermission, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'category', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


admin.site.register(Profile)
admin.site.register(DocumentPermission)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'document', 'action', 'status', 'timestamp')

    readonly_fields = (
        'actor',
        'document',
        'action',
        'status',
        'details',
        'timestamp'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
