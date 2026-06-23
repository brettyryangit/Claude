-- Data deletion on request (privacy requirement, spec section 8).
--
-- Deleting the user row cascades to goals, checkins, patterns, and messages_log
-- (all FKs are ON DELETE CASCADE). This is the manual admin path for v1; a
-- self-serve flow can come later.
--
-- Usage: set the number, review the SELECT, then run the DELETE.

-- Preview what will be removed:
select
  (select count(*) from goals       g  join users u on u.id = g.user_id  where u.whatsapp_number = '+61400000000') as goals,
  (select count(*) from messages_log ml join users u on u.id = ml.user_id where u.whatsapp_number = '+61400000000') as messages,
  (select count(*) from checkins c
     join goals g on g.id = c.goal_id
     join users u on u.id = g.user_id where u.whatsapp_number = '+61400000000') as checkins;

-- Permanently delete the user and all their data:
delete from users where whatsapp_number = '+61400000000';

-- Optionally also drop them from the allowlist:
-- delete from allowed_numbers where whatsapp_number = '+61400000000';
