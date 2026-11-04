
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import FileResponse, HttpResponseForbidden, HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User

from .models import Document, AuditLog, DocumentPermission, Profile

import os
import hashlib
import json
import io
import zipfile


def calculate_audit_hash(log):
    data = {
        'actor': log.actor_id,
        'document': log.document_id,
        'action': log.action,
        'status': log.status,
        'details': log.details,
        'timestamp': log.timestamp.isoformat(),
        'previous_hash': log.previous_hash
    }

    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def verify_uploaded_file(uploaded_file):
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension not in allowed_extensions:
        return "Only PDF, DOC, DOCX and TXT files are allowed."

    if uploaded_file.size == 0:
        return "Empty files cannot be uploaded."

    if uploaded_file.size > 5 * 1024 * 1024:
        return "File size must not exceed 5 MB."

    content = uploaded_file.read()
    uploaded_file.seek(0)

    if extension == '.pdf':
        if not content.startswith(b'%PDF-'):
            return "Invalid PDF file."

    elif extension == '.doc':
        signature = bytes.fromhex('D0CF11E0A1B11AE1')
        if not content.startswith(signature):
            return "Invalid DOC file."

    elif extension == '.docx':
        try:
            file_data = zipfile.ZipFile(io.BytesIO(content))
            if 'word/document.xml' not in file_data.namelist():
                return "Invalid DOCX file."
        except zipfile.BadZipFile:
            return "Invalid DOCX file."

    elif extension == '.txt':
        if b'\x00' in content:
            return "Invalid text file."

    uploaded_file.seek(0)
    return ""


@login_required
def verify_audit_logs(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden("Admin access only.")

    logs = AuditLog.objects.order_by('id')

    previous_hash = None
    checked_count = 0
    old_count = 0
    tampered = False

    for log in logs:

        if not log.record_hash:
            old_count += 1
            continue

        if previous_hash is None:
            if log.previous_hash not in ['', 'GENESIS']:
                tampered = True
                break
        elif log.previous_hash != previous_hash:
            tampered = True
            break

        expected_hash = calculate_audit_hash(log)

        if expected_hash != log.record_hash:
            tampered = True
            break

        previous_hash = log.record_hash
        checked_count += 1

    if tampered:
        result = "WARNING: Audit logs may have been modified!"
    else:
        result = "SUCCESS: All protected audit logs are valid."

    return HttpResponse(
        result +
        "\nProtected records checked: " + str(checked_count) +
        "\nOlder unprotected records: " + str(old_count),
        content_type="text/plain"
    )


@login_required
def upload_document(request):

    role = Profile.objects.filter(
        user=request.user
    ).values_list('role', flat=True).first()

    if role not in ['OWNER', 'ADMIN'] and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only owners and admins can upload documents."
        )

    error = ""

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip()
        uploaded_file = request.FILES.get('file')

        if not title or not category or not uploaded_file:
            error = "Please fill all fields."

        else:
            error = verify_uploaded_file(uploaded_file)

            if not error:
                document = Document.objects.create(
                    owner=request.user,
                    title=title,
                    category=category,
                    file=uploaded_file
                )

                AuditLog.objects.create(
                    actor=request.user,
                    document=document,
                    action='UPLOAD',
                    status='SUCCESS',
                    details='Document uploaded successfully'
                )

                return redirect('upload')

    return render(request, 'vault/upload.html', {
        'error': error
    })


@login_required
def download_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        is_deleted=False
    )

    allowed = (
        request.user.is_superuser or
        document.owner == request.user
    )

    permission = DocumentPermission.objects.filter(
        document=document,
        user=request.user
    ).first()

    if permission and (permission.can_read or permission.can_edit):
        allowed = True

    if not allowed:
        AuditLog.objects.create(
            actor=request.user,
            document=document,
            action='DOWNLOAD',
            status='DENIED',
            details='Unauthorized download attempt'
        )
        return HttpResponseForbidden("Access Denied")

    AuditLog.objects.create(
        actor=request.user,
        document=document,
        action='DOWNLOAD',
        status='SUCCESS',
        details='Document downloaded successfully'
    )

    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=document.file.name.split('/')[-1]
    )


def viewer_login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('document_list')

        return render(request, 'vault/login.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'vault/login.html')


@login_required
def document_list(request):

    documents = Document.objects.filter(
        owner=request.user,
        is_deleted=False
    ) | Document.objects.filter(
        documentpermission__user=request.user,
        documentpermission__can_read=True,
        is_deleted=False
    ) | Document.objects.filter(
        documentpermission__user=request.user,
        documentpermission__can_edit=True,
        is_deleted=False
    )

    documents = documents.distinct()

    for doc in documents:
        doc.can_delete = (
            request.user.is_superuser or
            doc.owner == request.user
        )

        doc.can_edit = (
            doc.can_delete or
            DocumentPermission.objects.filter(
                document=doc,
                user=request.user,
                can_edit=True
            ).exists()
        )

    return render(request, 'vault/document_list.html', {
        'documents': documents
    })


@login_required
def search_documents(request):

    query = request.GET.get('q', '')
    search_date = request.GET.get('date', '')

    if request.user.is_superuser:
        documents = Document.objects.filter(is_deleted=False)
    else:
        documents = Document.objects.filter(
            Q(owner=request.user) |
            Q(documentpermission__user=request.user,
              documentpermission__can_read=True) |
            Q(documentpermission__user=request.user,
              documentpermission__can_edit=True),
            is_deleted=False
        ).distinct()

    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(owner__username__icontains=query) |
            Q(category__icontains=query)
        )

    if search_date:
        documents = documents.filter(
            uploaded_at__date=search_date
        )

    return render(request, 'vault/search.html', {
        'documents': documents,
        'query': query,
        'search_date': search_date
    })


@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden("Admin access only.")

    total_documents = Document.objects.filter(
        is_deleted=False
    ).count()

    total_users = User.objects.count()
    total_permissions = DocumentPermission.objects.filter(
        document__is_deleted=False
    ).count()

    recent_activities = AuditLog.objects.order_by(
        '-timestamp'
    )[:10]

    return render(request, 'vault/dashboard.html', {
        'total_documents': total_documents,
        'total_users': total_users,
        'total_permissions': total_permissions,
        'recent_activities': recent_activities
    })


@login_required
def edit_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        is_deleted=False
    )

    permission = DocumentPermission.objects.filter(
        document=document,
        user=request.user,
        can_edit=True
    ).exists()

    allowed = (
        request.user.is_superuser or
        document.owner == request.user or
        permission
    )

    if not allowed:
        AuditLog.objects.create(
            actor=request.user,
            document=document,
            action='EDIT',
            status='DENIED',
            details='Unauthorized edit attempt'
        )
        return HttpResponseForbidden("Edit access denied.")

    if request.method == 'POST':

        document.title = request.POST.get('title')
        document.category = request.POST.get('category')

        document.save()

        AuditLog.objects.create(
            actor=request.user,
            document=document,
            action='EDIT',
            status='SUCCESS',
            details='Document details updated'
        )

        return redirect('document_list')

    return render(request, 'vault/edit.html', {
        'document': document
    })


@login_required
def delete_document(request, document_id):

    document = get_object_or_404(
        Document,
        id=document_id,
        is_deleted=False
    )

    allowed = (
        request.user.is_superuser or
        document.owner == request.user
    )

    if not allowed:
        AuditLog.objects.create(
            actor=request.user,
            document=document,
            action='DELETE',
            status='DENIED',
            details='Unauthorized delete attempt: ' + document.title
        )
        return HttpResponseForbidden("Delete access denied.")

    if request.method == 'POST':

        document_title = document.title

        AuditLog.objects.create(
            actor=request.user,
            document=document,
            action='DELETE',
            status='SUCCESS',
            details='Document moved to deleted status: ' + document_title
        )

        document.is_deleted = True
        document.save(update_fields=['is_deleted'])

        return redirect('document_list')

    return render(request, 'vault/delete.html', {
        'document': document
    })


@login_required
def manage_permissions(request):

    role = Profile.objects.filter(
        user=request.user
    ).values_list('role', flat=True).first()

    if role not in ['OWNER', 'ADMIN'] and not request.user.is_superuser:
        return HttpResponseForbidden("Permission management denied.")

    if request.user.is_superuser or role == 'ADMIN':
        documents = Document.objects.filter(is_deleted=False)
    else:
        documents = Document.objects.filter(
            owner=request.user,
            is_deleted=False
        )

    users = User.objects.filter(is_active=True)
    message = ""

    if request.method == 'POST':

        document_id = request.POST.get('document')
        username = request.POST.get('username')

        document = get_object_or_404(
            documents,
            id=document_id
        )

        user = get_object_or_404(
            users,
            username=username
        )

        if user == document.owner:
            message = "Owner already has access."

        else:
            can_read = request.POST.get('can_read') == 'on'
            can_edit = request.POST.get('can_edit') == 'on'

            if can_edit:
                can_read = True

            permission = DocumentPermission.objects.filter(
                document=document,
                user=user
            ).first()

            if can_read or can_edit:

                if permission:
                    permission.can_read = can_read
                    permission.can_edit = can_edit
                    permission.save()
                    action = 'PERMISSION_UPDATE'
                else:
                    DocumentPermission.objects.create(
                        document=document,
                        user=user,
                        can_read=can_read,
                        can_edit=can_edit
                    )
                    action = 'PERMISSION_GRANT'

                AuditLog.objects.create(
                    actor=request.user,
                    document=document,
                    action=action,
                    status='SUCCESS',
                    details='Permission updated for ' + user.username
                )

                message = "Permission saved successfully."

            else:
                if permission:
                    permission.delete()

                AuditLog.objects.create(
                    actor=request.user,
                    document=document,
                    action='PERMISSION_REVOKE',
                    status='SUCCESS',
                    details='Permission revoked for ' + user.username
                )

                message = "Permission revoked successfully."

    return render(request, 'vault/permissions.html', {
        'documents': documents,
        'users': users,
        'message': message
    })
