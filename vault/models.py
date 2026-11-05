
import hashlib
import json

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('OWNER', 'Document Owner'),
        ('VIEWER', 'Viewer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username


class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    cloudinary_public_id = models.CharField(
        max_length=255, blank=True, default=''
    )
    category = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class DocumentPermission(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    can_read = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    class Meta:
        unique_together = ('document', 'user')

    def __str__(self):
        return self.user.username + " - " + self.document.title


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    action = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    previous_hash = models.CharField(
        max_length=64, blank=True, default=''
    )
    record_hash = models.CharField(
        max_length=64, blank=True, default=''
    )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError(
                "Existing audit records cannot be edited."
            )

        previous = AuditLog.objects.order_by('-id').first()

        self.previous_hash = (
            previous.record_hash if previous else 'GENESIS'
        )

        super().save(*args, **kwargs)

        data = {
            'actor': self.actor_id,
            'document': self.document_id,
            'action': self.action,
            'status': self.status,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'previous_hash': self.previous_hash
        }

        content = json.dumps(data, sort_keys=True)

        self.record_hash = hashlib.sha256(
            content.encode()
        ).hexdigest()

        AuditLog.objects.filter(pk=self.pk).update(
            record_hash=self.record_hash
        )

    def __str__(self):
        return self.action + " - " + self.status
