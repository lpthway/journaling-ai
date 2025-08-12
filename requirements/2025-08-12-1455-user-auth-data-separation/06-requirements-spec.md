# User Authentication and Data Separation Requirements Specification

**Date:** 2025-08-12 15:15  
**Project:** Journaling AI - Security Enhancement  
**Phase:** Implementation Ready

## Problem Statement

The journaling AI system currently has critical security vulnerabilities:
- Users can access data belonging to other users
- No data encryption for sensitive journal content
- Missing user context in data models (entries, topics, sessions)
- No audit logging for security monitoring
- No data retention or user deletion capabilities

## Solution Overview

Implement comprehensive user data separation with hybrid encryption, admin oversight capabilities, and future-ready zero-knowledge architecture.

## Functional Requirements

### 1. User Data Separation
- **FR-1.1**: All entries must be associated with a specific user via user_id foreign key
- **FR-1.2**: All topics must be associated with a specific user via user_id foreign key  
- **FR-1.3**: All chat sessions must be associated with a specific user via user_id foreign key
- **FR-1.4**: Users can only access their own data by default
- **FR-1.5**: Migrate existing data to proper user ownership

### 2. Hybrid Encryption System
- **FR-2.1**: Encrypt journal entry content and titles before database storage
- **FR-2.2**: Encrypt chat session messages before database storage
- **FR-2.3**: Temporarily decrypt data for AI analysis with user consent
- **FR-2.4**: Re-encrypt AI analysis results before storage
- **FR-2.5**: Support client-side decryption for user data access

### 3. Admin Access Control
- **FR-3.1**: Admin users can access all user data via master keys
- **FR-3.2**: All admin data access must be logged in audit system
- **FR-3.3**: Admin access requires proper authentication and authorization
- **FR-3.4**: Design supports future migration to user-consent-only access

### 4. Data Management
- **FR-4.1**: Users can delete their account and all associated data
- **FR-4.2**: Users can export all their data in portable format
- **FR-4.3**: Implement data retention policies for automatic cleanup
- **FR-4.4**: Support "right to be forgotten" complete data purging

### 5. Audit Logging
- **FR-5.1**: Log all user actions (login, data CRUD, exports, deletions)
- **FR-5.2**: Log all admin actions (data access, user management, system changes)
- **FR-5.3**: Log all AI processing events (decryption, analysis, re-encryption)
- **FR-5.4**: Generate compliance reports from audit data

## Technical Requirements

### 1. Database Schema Changes
- **TR-1.1**: Add `user_id UUID NOT NULL` foreign key to `entries` table referencing `auth_users.id`
- **TR-1.2**: Add `user_id UUID NOT NULL` foreign key to `topics` table referencing `auth_users.id`
- **TR-1.3**: Add `user_id UUID NOT NULL` foreign key to `sessions` table referencing `auth_users.id`
- **TR-1.4**: Create database migration for existing data ownership assignment
- **TR-1.5**: Add database constraints to enforce user data separation

### 2. Encryption Service Architecture
- **TR-2.1**: Create `backend/app/encryption/` module with dedicated encryption service
- **TR-2.2**: Implement separate key management system isolated from JWT configuration
- **TR-2.3**: Support admin master keys and user-derived keys
- **TR-2.4**: Design for future zero-knowledge architecture migration
- **TR-2.5**: Use industry-standard encryption algorithms (AES-256)

### 3. API Modifications
- **TR-3.1**: Update all entry endpoints to filter by authenticated user_id
- **TR-3.2**: Update all topic endpoints to filter by authenticated user_id
- **TR-3.3**: Update all session endpoints to filter by authenticated user_id
- **TR-3.4**: Update all insights endpoints to only process user's own data
- **TR-3.5**: Remove `DEFAULT_USER_ID` from frontend API service

### 4. Audit Database
- **TR-4.1**: Create separate audit database with different access controls
- **TR-4.2**: Implement immutable audit log tables
- **TR-4.3**: Create audit service for centralized logging
- **TR-4.4**: Set up audit log retention and cleanup policies

### 5. Frontend Security
- **TR-5.1**: Update `AuthContext` to provide user context to all API calls
- **TR-5.2**: Implement client-side encryption/decryption utilities
- **TR-5.3**: Add user data export and deletion UI components
- **TR-5.4**: Display audit log access for user transparency

## Implementation Hints and Patterns

### 1. Follow Existing Patterns
- Extend `AuthUser` model at `backend/app/auth/models.py` for user relationships
- Use existing dependency injection patterns from `backend/app/auth/dependencies.py`
- Follow existing API route patterns in `backend/app/auth/routes.py`
- Maintain consistency with current admin dashboard structure

### 2. Database Migration Strategy
```sql
-- Example migration structure
ALTER TABLE entries ADD COLUMN user_id UUID REFERENCES auth_users(id);
ALTER TABLE topics ADD COLUMN user_id UUID REFERENCES auth_users(id);
ALTER TABLE sessions ADD COLUMN user_id UUID REFERENCES auth_users(id);

-- Update existing data with appropriate user assignment
-- Add NOT NULL constraints after data migration
```

### 3. Encryption Service Interface
```python
# Example encryption service structure
class EncryptionService:
    def encrypt_user_data(self, data: str, user_id: str) -> str
    def decrypt_user_data(self, encrypted_data: str, user_id: str) -> str
    def decrypt_for_admin(self, encrypted_data: str) -> str
    def decrypt_for_ai_analysis(self, encrypted_data: str, user_consent: bool) -> str
```

### 4. Audit Service Interface
```python
# Example audit service structure
class AuditService:
    def log_user_action(self, user_id: str, action: str, resource: str, details: dict)
    def log_admin_action(self, admin_id: str, action: str, target_user: str, details: dict)
    def log_ai_processing(self, user_id: str, operation: str, data_types: list)
```

## Acceptance Criteria

### 1. Data Separation
- [ ] Users cannot access other users' entries, topics, or sessions
- [ ] All API endpoints respect user ownership boundaries
- [ ] Existing data properly migrated to user ownership
- [ ] Database constraints prevent cross-user data access

### 2. Encryption
- [ ] All sensitive data encrypted before database storage
- [ ] Admin can decrypt data with master keys and proper audit logging
- [ ] AI analysis works with hybrid encryption approach
- [ ] Client-side decryption functions correctly

### 3. Admin Controls
- [ ] Admin dashboard shows user data access capabilities
- [ ] All admin actions logged in separate audit database
- [ ] Admin access requires proper authentication
- [ ] Future migration path to user-consent-only is preserved

### 4. Data Rights
- [ ] Users can export all their data in usable format
- [ ] Account deletion removes all user data completely
- [ ] Data retention policies automatically clean up old data
- [ ] Audit logs maintain compliance requirements

### 5. Security
- [ ] No unauthorized data access possible
- [ ] Encryption keys properly managed and rotated
- [ ] Audit logs tamper-proof and immutable
- [ ] System passes security review for personal data handling

## Assumptions

- Existing authentication system remains the foundation for user identity
- PostgreSQL database continues to be the primary data store
- Frontend React application maintains current user experience patterns
- Admin users are trusted personnel with legitimate support needs
- Future migration to zero-knowledge architecture is a planned enhancement
- Compliance with GDPR and similar privacy regulations is required

## Security Considerations

- All encryption keys must be rotated regularly
- Audit logs must be protected from tampering
- Admin access must be logged and monitored
- Data export/deletion must be irreversible when requested
- System must support security audits and penetration testing

## Performance Considerations

- Encryption/decryption operations may impact response times
- Database queries must be optimized for user-filtered data
- Audit logging must not significantly impact application performance
- AI analysis may require optimization for encrypted data processing