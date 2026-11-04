# TrustVault – AI Prompt and Development Log

This document records AI-assisted development work completed for the TrustVault project.

**Note:** The entries below are project-development summaries. Update the dates, actual tool outputs, errors, corrections, and commit links to match your real development history before submission.

## Entry 1 – Project Structure and Django Setup

**Date:** 04 November 2026

**Prompt Used:**

"Help me create a beginner-friendly Django project for secure document sharing with administrator, document owner, and viewer roles."

**Output Summary:**

Created the Django project structure with a `config` project and a `vault` application. Set up the initial database models and application configuration.

**Error or Issue:**

The application required database tables to be created.

**Correction:**

Ran Django migrations using:

`py manage.py makemigrations`

`py manage.py migrate`

**Commit Link:** To be added after pushing the code to GitHub.

## Entry 2 – Document Authorization

**Date:** 04 November 2026

**Prompt Used:**

"Add server-side authorization so viewers cannot download, edit, or delete documents without the required permission."

**Output Summary:**

Added permission checks for document access, downloading, editing, and deleting.

**Error or Issue:**

Unauthorized users needed to be blocked even when they tried to access a document directly through its URL.

**Correction:**

Added authorization checks inside the Django views and tested unauthorized access.

**Commit Link:** To be added after pushing the code to GitHub.

## Entry 3 – Audit Logging and Verification

**Date:** 04 November 2026

**Prompt Used:**

"Add audit logging for document activities and use SHA-256 hash linking to detect modifications to protected audit records."

**Output Summary:**

Added audit records containing the actor, document, action, status, details, and timestamp. Added hash-based verification.

**Error or Issue:**

Audit records needed a way to detect changes to their stored information.

**Correction:**

Added `previous_hash` and `record_hash` fields and implemented audit verification. Added a test to check whether modification of a protected record is detected.

**Commit Link:** To be added after pushing the code to GitHub.

## Entry 4 – File Upload Validation

**Date:** 04 November 2026

**Prompt Used:**

"Add file validation to allow only PDF, DOC, DOCX, and TXT files. Reject empty files and files larger than 5 MB."

**Output Summary:**

Added file extension, size, empty-file, and basic file-format checks.

**Error or Issue:**

Unsupported file formats needed to be rejected.

**Correction:**

Added validation before saving uploaded documents. Tested supported and unsupported file types.

**Commit Link:** To be added after pushing the code to GitHub.

## Entry 5 – Automated Testing

**Date:** 04 November 2026

**Prompt Used:**

"Create Django tests to verify unauthorized document access, permission revocation, denied download logging, and audit-log modification detection."

**Output Summary:**

Added automated tests for document authorization and audit verification.

**Error or Issue:**

The application needed tests to confirm that security restrictions worked correctly.

**Correction:**

Ran:

`py manage.py test vault`

All six tests passed.

**Commit Link:** To be added after pushing the code to GitHub.

## Development Note

AI assistance was used for learning, code suggestions, debugging, and documentation. The generated code was reviewed and tested during development. Commit links will be added after the project is pushed to GitHub.