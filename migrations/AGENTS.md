# Migrations

Issue: E8-1. Database migrations for the move from SQLite to Postgres. Each migration is forward-only, named with a sequence number, and has a test that runs it on an empty database. Never put real data or secrets in a migration.
