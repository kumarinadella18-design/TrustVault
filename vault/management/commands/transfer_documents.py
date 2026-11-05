
from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections, transaction

from vault.models import Document, DocumentPermission, AuditLog


class Command(BaseCommand):
    help = "Transfer local TrustVault data to Render PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Perform actual transfer"
        )

    def handle(self, *args, **options):

        # Check Render PostgreSQL connection
        if connections["default"].vendor != "postgresql":
            raise CommandError(
                "DATABASE_URL must point to Render PostgreSQL."
            )

        # Check local SQLite database
        source_path = settings.BASE_DIR / "db.sqlite3"

        if not source_path.exists():
            raise CommandError("Local db.sqlite3 not found.")

        # Configure local SQLite source database
        settings.DATABASES["source"] = (
            settings.DATABASES["default"].copy()
        )

        settings.DATABASES["source"].update({
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(source_path),
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
            "OPTIONS": {},
        })

        # Read source records
        documents = list(
            Document.objects.using("source")
            .select_related("owner").all()
        )

        permissions = list(
            DocumentPermission.objects.using("source")
            .select_related("user", "document").all()
        )

        logs = list(
            AuditLog.objects.using("source")
            .select_related("actor").all()
        )

        if not documents:
            raise CommandError("No local documents found.")

        # Stop if production already contains records
        if (
            Document.objects.using("default").exists()
            or DocumentPermission.objects.using("default").exists()
            or AuditLog.objects.using("default").exists()
        ):
            raise CommandError(
                "Production already contains records. Transfer stopped."
            )

        # Collect required usernames
        usernames = set()

        for doc in documents:
            usernames.add(doc.owner.username)

        for permission in permissions:
            usernames.add(permission.user.username)

        for log in logs:
            if log.actor:
                usernames.add(log.actor.username)

        # Match existing Render users
        target_users = {
            user.username: user
            for user in User.objects.using("default").filter(
                username__in=usernames
            )
        }

        missing = usernames - set(target_users.keys())

        if missing:
            raise CommandError(
                "Missing Render users: " + ", ".join(sorted(missing))
            )

        # Validate local files
        for doc in documents:
            if not doc.cloudinary_public_id:
                if not doc.file or not Path(doc.file.path).is_file():
                    raise CommandError(
                        f"Local file missing for document {doc.id}"
                    )

        self.stdout.write("LOCAL DOCUMENTS:")

        for doc in documents:
            self.stdout.write(
                f"{doc.id}: {doc.title} - {doc.owner.username}"
            )

        self.stdout.write(f"Permissions found: {len(permissions)}")
        self.stdout.write(f"Audit logs found: {len(logs)}")

        # Dry run: no uploads or database changes
        if not options["apply"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "DRY RUN SUCCESSFUL. No data transferred."
                )
            )
            self.stdout.write(
                "After checking the output, use --apply for transfer."
            )
            return

        # Verify Cloudinary configuration
        if not cloudinary.config().cloud_name:
            raise CommandError("Cloudinary is not configured.")

        # Upload or verify document files
        cloud_ids = {}

        for doc in documents:

            if doc.cloudinary_public_id:
                try:
                    cloudinary.api.resource(
                        doc.cloudinary_public_id,
                        resource_type="raw",
                        type="authenticated"
                    )
                except Exception as e:
                    raise CommandError(
                        f"Cloudinary verification failed for "
                        f"document {doc.id}: {e}"
                    )

                cloud_ids[doc.id] = doc.cloudinary_public_id

            else:
                try:
                    result = cloudinary.uploader.upload(
                        doc.file.path,
                        resource_type="raw",
                        type="authenticated"
                    )

                    cloud_ids[doc.id] = result["public_id"]

                    self.stdout.write(
                        f"Cloudinary upload completed for document {doc.id}."
                    )

                except Exception as e:
                    raise CommandError(
                        f"Cloudinary upload failed for document "
                        f"{doc.id}: {e}"
                    )

        # Transfer database records
        try:
            with transaction.atomic(using="default"):

                new_documents = []

                for doc in documents:
                    new_documents.append(
                        Document(
                            id=doc.id,
                            owner=target_users[doc.owner.username],
                            title=doc.title,
                            file=doc.file.name,
                            cloudinary_public_id=cloud_ids[doc.id],
                            category=doc.category,
                            uploaded_at=doc.uploaded_at,
                            is_deleted=doc.is_deleted
                        )
                    )

                Document.objects.using("default").bulk_create(
                    new_documents
                )

                new_permissions = []

                for permission in permissions:
                    new_permissions.append(
                        DocumentPermission(
                            id=permission.id,
                            document_id=permission.document_id,
                            user=target_users[permission.user.username],
                            can_read=permission.can_read,
                            can_edit=permission.can_edit
                        )
                    )

                DocumentPermission.objects.using(
                    "default"
                ).bulk_create(new_permissions)

                new_logs = []

                for log in logs:
                    actor = None

                    if log.actor:
                        actor = target_users[log.actor.username]

                    new_logs.append(
                        AuditLog(
                            id=log.id,
                            actor=actor,
                            document_id=log.document_id,
                            action=log.action,
                            status=log.status,
                            details=log.details,
                            timestamp=log.timestamp,
                            previous_hash=log.previous_hash,
                            record_hash=log.record_hash
                        )
                    )

                # Preserve original audit hashes
                AuditLog.objects.using("default").bulk_create(
                    new_logs
                )

                # Reset PostgreSQL ID sequences
                models = [
                    Document,
                    DocumentPermission,
                    AuditLog
                ]

                sql_list = connections[
                    "default"
                ].ops.sequence_reset_sql(no_style(), models)

                with connections["default"].cursor() as cursor:
                    for sql in sql_list:
                        cursor.execute(sql)

        except Exception as e:
            raise CommandError(f"Database transfer failed: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                "TRANSFER COMPLETED SUCCESSFULLY!"
            )
        )

        self.stdout.write(f"Documents transferred: {len(documents)}")
        self.stdout.write(f"Permissions transferred: {len(permissions)}")
        self.stdout.write(f"Audit logs transferred: {len(logs)}")
