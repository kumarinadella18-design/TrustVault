
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document, Profile, DocumentPermission, AuditLog


class TrustVaultSecurityTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1',
            password='testpass123'
        )

        self.viewer = User.objects.create_user(
            username='viewer1',
            password='testpass123'
        )

        Profile.objects.create(user=self.owner, role='OWNER')
        Profile.objects.create(user=self.viewer, role='VIEWER')

        test_file = SimpleUploadedFile(
            'test.txt',
            b'Test document content',
            content_type='text/plain'
        )

        self.document = Document.objects.create(
            owner=self.owner,
            title='Private Document',
            category='General',
            file=test_file
        )

    def test_unauthorized_download(self):
        self.client.force_login(self.viewer)

        response = self.client.get(
            f'/download/{self.document.id}/'
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthorized_edit(self):
        self.client.force_login(self.viewer)

        response = self.client.get(
            f'/edit/{self.document.id}/'
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthorized_delete(self):
        self.client.force_login(self.viewer)

        response = self.client.get(
            f'/delete/{self.document.id}/'
        )

        self.assertEqual(response.status_code, 403)

    def test_revoked_permission_blocks_download(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=False,
            can_edit=False
        )

        self.client.force_login(self.viewer)

        response = self.client.get(
            f'/download/{self.document.id}/'
        )

        self.assertEqual(response.status_code, 403)

    def test_denied_download_is_logged(self):
        self.client.force_login(self.viewer)

        self.client.get(f'/download/{self.document.id}/')

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.viewer,
                document=self.document,
                action='DOWNLOAD',
                status='DENIED'
            ).exists()
        )

    def test_tampered_audit_log_is_detected(self):
        admin = User.objects.create_superuser(
            username='testadmin',
            email='admin@example.com',
            password='testpass123'
        )

        log = AuditLog.objects.create(
            actor=self.owner,
            document=self.document,
            action='UPLOAD',
            status='SUCCESS',
            details='Original upload'
        )

        AuditLog.objects.filter(pk=log.pk).update(
            details='Modified upload'
        )

        self.client.force_login(admin)

        response = self.client.get('/verify-audit/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'WARNING: Audit logs may have been modified!'
        )

    def test_existing_audit_log_cannot_be_edited(self):
        log = AuditLog.objects.create(
            actor=self.owner,
            document=self.document,
            action='UPLOAD',
            status='SUCCESS',
            details='Original upload'
        )

        log.details = 'Changed upload'

        with self.assertRaises(ValueError):
            log.save()

    def test_document_soft_delete(self):
        self.client.force_login(self.owner)

        self.client.post(
            f'/delete/{self.document.id}/'
        )

        self.document.refresh_from_db()

        self.assertTrue(self.document.is_deleted)
        self.assertTrue(
            Document.objects.filter(id=self.document.id).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                document=self.document,
                action='DELETE',
                status='SUCCESS'
            ).exists()
        )

    def test_deleted_document_cannot_be_downloaded(self):
        self.document.is_deleted = True
        self.document.save(update_fields=['is_deleted'])

        self.client.force_login(self.owner)

        response = self.client.get(
            f'/download/{self.document.id}/'
        )

        self.assertEqual(response.status_code, 404)
