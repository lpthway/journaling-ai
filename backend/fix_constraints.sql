-- Fix foreign key constraints to reference auth_users instead of users

-- Drop existing constraints
ALTER TABLE entries DROP CONSTRAINT IF EXISTS entries_user_id_fkey;
ALTER TABLE topics DROP CONSTRAINT IF EXISTS topics_user_id_fkey;
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;
ALTER TABLE entry_templates DROP CONSTRAINT IF EXISTS entry_templates_created_by_user_id_fkey;

-- Add new constraints referencing auth_users
ALTER TABLE entries ADD CONSTRAINT entries_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE;

ALTER TABLE topics ADD CONSTRAINT topics_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE;

ALTER TABLE chat_sessions ADD CONSTRAINT chat_sessions_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE;

ALTER TABLE entry_templates ADD CONSTRAINT entry_templates_created_by_user_id_fkey 
    FOREIGN KEY (created_by_user_id) REFERENCES auth_users(id) ON DELETE SET NULL;