# Expert Detail Questions

**Date:** 2025-08-12 15:10

## Q6: Should we extend the existing AuthUser model at backend/app/auth/models.py or create new user relationships?
**Default if unknown:** Yes (maintains architectural consistency with existing JWT authentication system)

## Q7: Should we implement encryption using the existing security.py patterns or add a new encryption service?
**Default if unknown:** No (create dedicated encryption service for separation of concerns)

## Q8: Should admin master keys be stored in the same security configuration as JWT secrets in backend/app/core/config.py?
**Default if unknown:** No (separate key management system for enhanced security)

## Q9: Should we add user_id foreign keys to the existing database tables or create new tables for user data relationships?
**Default if unknown:** Yes (modify existing tables to maintain data consistency and avoid duplication)

## Q10: Should audit logs be stored in the same database as user data or in a separate audit database?
**Default if unknown:** No (separate audit database for security and compliance isolation)