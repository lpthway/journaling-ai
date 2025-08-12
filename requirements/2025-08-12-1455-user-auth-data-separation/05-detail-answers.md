# Detail Answers

**Date:** 2025-08-12 15:15

## Q6: Should we extend the existing AuthUser model at backend/app/auth/models.py or create new user relationships?
**Answer:** Yes
**Decision:** Extend existing AuthUser model for consistency with JWT authentication system

## Q7: Should we implement encryption using the existing security.py patterns or add a new encryption service?
**Answer:** No, use Option B
**Decision:** Create dedicated encryption service at `backend/app/encryption/` for separation of concerns

## Q8: Should admin master keys be stored in the same security configuration as JWT secrets in backend/app/core/config.py?
**Answer:** No, use Option B
**Decision:** Separate key management system for enhanced security
**Future Path:** Design for eventual migration to user-consent-only access (zero-knowledge architecture)

## Q9: Should we add user_id foreign keys to the existing database tables or create new tables for user data relationships?
**Answer:** Yes, use Option A
**Decision:** Modify existing tables (entries, topics, sessions) to add user_id foreign keys

## Q10: Should audit logs be stored in the same database as user data or in a separate audit database?
**Answer:** No, use Option B
**Decision:** Separate audit database for security isolation and compliance protection