-- data/sql/seed_sprint15.sql
-- Example mass-seeding SQL snippets for postgres.

INSERT INTO users (id, name, role, email) VALUES
  ('11111111-1111-1111-1111-111111111111','Admin One','admin','admin@rentora.test'),
  ('22222222-2222-2222-2222-222222222222','Owner A','owner','ownerA@rentora.test'),
  ('33333333-3333-3333-3333-333333333333','Tenant X','tenant','tenantX@rentora.test');

INSERT INTO properties (id, owner_id, title, status, available_from) VALUES
  ('p-100','22222222-2222-2222-2222-222222222222','1BHK Koramangala','occupied','2026-06-01');

INSERT INTO payment_transactions (id, tenant_id, owner_id, agreement_id, amount, payment_type, status, created_at)
 VALUES ('t-100','33333333-3333-3333-3333-333333333333','22222222-2222-2222-2222-222222222222','agr-100',50000,'deposit','success','2026-03-01');
