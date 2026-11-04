# TrustVault – Secure Document Sharing System

## 1. Project Overview

TrustVault is a secure document-sharing web application developed using Python and Django. It allows users to upload, manage, search, and share documents with authorized users.

The system provides role-based access control and maintains activity records to help protect documents from unauthorized access.

## 2. Main Features

- Secure document upload and download.
- Document search by title and category.
- Role-based access control.
- Read and Edit permissions for individual users.
- Granting and revoking document permissions.
- Admin dashboard to view users, documents, permissions, and activities.
- Audit logs for recording document activities.
- File validation for supported document formats.

## 3. User Roles

### Administrator
- View system information.
- Monitor document activities.
- Manage users through Django Admin.
- Verify protected audit log records.

### Document Owner
- Upload documents.
- View and manage owned documents.
- Edit and delete owned documents.
- Grant or revoke permissions.

### Viewer
- View documents when Read permission is granted.
- Download authorized documents.
- Cannot edit or delete documents without permission.

## 4. Technologies Used

- **Programming Language:** Python
- **Framework:** Django
- **Frontend:** HTML, CSS
- **Database:** Local development database
- **Development Tool:** Visual Studio Code
- **Version Control:** Git and GitHub (planned)

## 5. File Validation

TrustVault supports the following file formats:

- PDF
- DOC
- DOCX
- TXT

Validation checks include:
- File extension.
- Empty file checking.
- Maximum file size of 5 MB.
- Basic file-format signature checking.

## 6. Audit Logging

TrustVault records important activities, including document uploads, downloads, edits, deletions, and permission changes.

The audit log includes:
- User who performed the activity.
- Document details.
- Action performed.
- Activity status.
- Date and time.

The project uses SHA-256 hash linking to help detect modifications to protected audit records. This is a tamper-evident prototype, not a guarantee of complete immutability.

## 7. Project Structure

```text
TrustVault/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── vault/
│   ├── migrations/
│   ├── templates/
│   │   └── vault/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── manage.py
├── README.md
└── .venv/
```

## 8. Installation and Setup

### Step 1: Install Python

Install Python and verify the installation:

```powershell
py --version
```

### Step 2: Create a virtual environment

```powershell
py -m venv .venv
```

### Step 3: Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 4: Install Django

```powershell
py -m pip install django
```

### Step 5: Apply database migrations

```powershell
py manage.py migrate
```

### Step 6: Create an administrator account

```powershell
py manage.py createsuperuser
```

### Step 7: Start the development server

```powershell
py manage.py runserver
```

Open the following address in your browser:

```text
http://127.0.0.1:8000/
```

## 9. Important Application URLs

| Page | URL |
|---|---|
| Django Admin | `/admin/` |
| Document Upload | `/upload/` |
| Document List | `/documents/` |
| Search Documents | `/search/` |
| Admin Dashboard | `/dashboard/` |
| Manage Permissions | `/permissions/` |
| Verify Audit Logs | `/verify-audit/` |

## 10. Testing

Run the project checks:

```powershell
py manage.py check
```

Run the application tests:

```powershell
py manage.py test vault
```

The tests cover unauthorized document access, permission revocation, denied download logging, and audit-log modification detection.

## 11. Security Notes and Future Enhancements

The current project is a development prototype. Future improvements include:

- PostgreSQL database integration.
- Production deployment.
- Stronger file scanning and malware detection.
- Improved audit-log protection.
- Additional security and access-control tests.
- Better user interface and responsive design.

## 12. Conclusion

TrustVault provides a role-based document-sharing system with document permissions, file validation, activity tracking, and audit-log verification. It aims to make document sharing more organized and secure.