# Phase 1 Architecture

The repository is organized as a frontend/backend monorepo. Flask owns HTTP and persistence concerns; SQLAlchemy models define relational data; the algorithm package is isolated for manual implementations in Phase 3. SQLite is the development database. PostgreSQL remains an optional production target through the same SQLAlchemy configuration.

## Boundaries

- `app/models`: persistence entities and constraints
- `app/routes`: HTTP route modules
- `app/services`: workflow services to be added in Phase 2 and 4
- `app/algorithms`: empty interfaces for the four required algorithms
- `app/security`: security services to be added in Phase 2
- `app/utils`: shared infrastructure helpers

## Local database behavior

Local migrations and tests use SQLite and require no database service. The allocation workflow retains `with_for_update()` and explicit inventory revalidation for database engines that support row-level locking. SQLite does not provide PostgreSQL-equivalent concurrent row-lock semantics, so SQLite verification does not claim to prove production concurrency behavior.
