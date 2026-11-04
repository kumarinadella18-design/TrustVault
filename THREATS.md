# TrustVault – Threat Model and Security Analysis

## 1. Introduction

TrustVault is a secure document-sharing application developed using Python and Django. It allows document owners to upload and share documents with authorized users.

This document identifies possible security threats and explains the security measures implemented or planned to reduce those risks.

## 2. Assets to Protect

The important assets in TrustVault are:

- Uploaded documents.
- User accounts and login credentials.
- Document permissions.
- User and document information.
- Audit logs.
- Application database.

## 3. Possible Security Threats

### Threat 1: Unauthorized Document Access

**Description:** An unauthorized user may try to view or download another user's document.

**Impact:** Private documents may be exposed.

**Prevention:**
- Check user permissions before allowing access.
- Allow document owners to control access.
- Deny access when the user does not have permission.

**Current Status:** Basic authorization checks are implemented and tested.

### Threat 2: Unauthorized Document Modification

**Description:** A viewer may try to edit or delete a document without permission.

**Impact:** Important document information may be changed or lost.

**Prevention:**
- Only document owners and authorized editors can edit documents.
- Only document owners and administrators can delete documents.
- Verify authorization on the server.

**Current Status:** Basic edit and delete authorization checks are implemented and tested.

### Threat 3: Permission Misuse

**Description:** A user may continue accessing a document after their permission has been revoked.

**Impact:** Unauthorized access to private documents.

**Prevention:**
- Check permissions whenever a document is accessed.
- Remove permissions when the owner revokes access.
- Do not rely only on previously generated links.

**Current Status:** Permission revocation and access denial are implemented and tested.

### Threat 4: Invalid File Upload

**Description:** A user may upload unsupported, empty, oversized, or incorrectly formatted files.

**Impact:** Invalid or potentially harmful files may enter the application.

**Prevention:**
