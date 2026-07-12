-- Idempotent init: create nautobot user and database if they don't exist
SELECT 'CREATE USER nautobot WITH PASSWORD ''nautobot'''
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nautobot')\gexec

SELECT 'CREATE DATABASE nautobot OWNER nautobot'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nautobot')\gexec
