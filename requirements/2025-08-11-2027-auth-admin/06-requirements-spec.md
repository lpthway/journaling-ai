# Requirements Specification: Authentication & Admin Area Enhancement

**Project:** Journaling AI  
**Generated:** 2025-08-11 20:27  
**Status:** Ready for Implementation

## Problem Statement

The journaling AI application currently has a comprehensive authentication system but lacks:
1. A complete admin interface for user management
2. Dynamic user context (currently uses hardcoded `default_user`)
3. Enhanced role-based permissions
4. Admin session management capabilities

## Solution Overview

Enhance the existing authentication system by:
1. Extending current auth models with role management
2. Building a React-based admin interface
3. Migrating all hardcoded user references to dynamic JWT-based authentication
4. Adding comprehensive admin session and security management

## Functional Requirements

### FR1: Enhanced User Management
- ✅ **Existing**: Basic admin endpoints at `/admin/users` and `/admin/login-attempts`
- 🔧 **Enhance**: Full CRUD operations (create, edit, disable/enable users)
- 🔧 **Add**: User role assignment interface
- 🔧 **Add**: Bulk user operations

### FR2: Dynamic User Authentication
- ✅ **Existing**: Complete JWT authentication system
- 🔧 **Migrate**: Replace 944 hardcoded `user_id`/`default_user` references
- 🔧 **Integrate**: All API endpoints to use current user from JWT
- 🔧 **Update**: Frontend to use authenticated user context

### FR3: Role-Based Access Control
- ✅ **Existing**: Basic user/superuser model
- 🔧 **Extend**: AuthUser model with extensible role system
- 🔧 **Implement**: Role-based endpoint protection
- 🔧 **Future-proof**: Design for intermediate roles (moderator, etc.)

### FR4: Admin Session Management
- ✅ **Existing**: RefreshToken tracking system
- 🔧 **Add**: Admin view of all active user sessions
- 🔧 **Add**: Force logout capability for specific sessions
- 🔧 **Add**: Session security monitoring

### FR5: Security Monitoring Dashboard
- ✅ **Existing**: LoginAttempt tracking
- 🔧 **Add**: Admin dashboard for login attempts
- 🔧 **Add**: Security alerts and suspicious activity detection
- 🔧 **Add**: IP-based access monitoring

## Technical Requirements

### Backend Enhancement (`/backend/app/auth/`)

#### TR1: Role Model Extension
- **File**: `backend/app/auth/models.py:17-110`
- **Action**: Add `role` field to AuthUser model
- **Pattern**: Use existing SQLAlchemy patterns

#### TR2: Enhanced Admin Routes
- **File**: `backend/app/auth/routes.py:474-560`
- **Action**: Extend admin router with:
  - `PUT /admin/users/{user_id}` - Edit user
  - `DELETE /admin/users/{user_id}` - Disable user
  - `GET /admin/sessions` - List active sessions
  - `DELETE /admin/sessions/{session_id}` - Force logout

#### TR3: Service Layer Enhancement
- **File**: `backend/app/auth/service.py:51-610`
- **Action**: Add admin management methods
- **Pattern**: Follow existing async/await patterns

### User ID Migration (944 references across 89 files)

#### TR4: Backend Services Migration
- **Priority Files**:
  - `services/unified_database_service.py:42`
  - `services/advanced_ai_service.py:13`
  - `api/entries.py:16`
  - `api/sessions.py:3`
- **Action**: Replace hardcoded IDs with `CurrentUser` dependency

#### TR5: Frontend Migration
- **Files**: 
  - `frontend/src/config/user.js:3`
  - `frontend/src/services/api.js:7`
  - `frontend/src/services/analyticsApi.js:2`
- **Action**: Implement auth context and remove hardcoded DEFAULT_USER_ID

### Frontend Admin Interface

#### TR6: Admin Pages
- **Location**: `frontend/src/pages/`
- **Components**:
  - `AdminDashboard.jsx` - Main admin interface
  - `UserManagement.jsx` - User CRUD operations
  - `SessionManagement.jsx` - Active session monitoring
  - `SecurityMonitoring.jsx` - Login attempts and security

#### TR7: Authentication Integration
- **Files**: `frontend/src/services/api.js`, `frontend/src/services/api.ts`
- **Action**: Add JWT token management and auth state

## Implementation Hints

### Database Migration Required
- **File**: New migration in `backend/alembic/versions/`
- **Content**: Add role column to auth_users table
- **Pattern**: Follow `2025_08_08_1551_342ebd797ac1_add_authentication_tables.py`

### FastAPI Patterns
- Use existing `CurrentUser`, `CurrentSuperuser` dependencies
- Follow rate limiting patterns from `dependencies.py:195-261`
- Maintain error handling patterns from `routes.py:71-80`

### React Patterns
- Follow existing page structure in `frontend/src/pages/`
- Use existing API service patterns from `frontend/src/services/`
- Integrate with existing component styles

## Acceptance Criteria

### AC1: Authentication Integration
- [ ] All 944 hardcoded user_id references replaced with dynamic context
- [ ] Frontend authentication state management implemented
- [ ] JWT tokens properly stored and used for API calls

### AC2: Admin Interface
- [ ] Complete admin dashboard accessible to superusers
- [ ] User management interface with create/edit/disable functionality
- [ ] Session management with forced logout capability
- [ ] Security monitoring dashboard with login attempt history

### AC3: Role System
- [ ] AuthUser model extended with role field
- [ ] Role-based endpoint protection implemented
- [ ] Admin interface for role assignment

### AC4: Security & Performance
- [ ] All existing rate limiting maintained
- [ ] Security patterns preserved (password hashing, JWT validation)
- [ ] Database performance maintained with proper indexing

## Assumptions

1. **Email Service**: Assuming email service configuration exists for password reset functionality
2. **Frontend Routing**: Assuming React router can be extended for admin routes
3. **Database Permissions**: Assuming database user has necessary privileges for schema changes
4. **Deployment**: Assuming standard development/production deployment pipeline

## Dependencies

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Jose JWT, Passlib
- **Frontend**: React, existing component patterns
- **Database**: PostgreSQL with existing auth tables
- **Security**: Existing JWT and bcrypt implementations