---
description: Create database migration
argument-hint: [migration name]
---

Create database migration: $ARGUMENTS

1. Generate migration file with timestamp
2. Define up migration (schema changes)
3. Define down migration (rollback)
4. Add indexes for query optimization
5. Set up constraints and foreign keys
6. Handle data transformation if needed
7. Test migration locally
8. Document breaking changes

Migration should handle:
- Schema changes safely
- Data preservation
- Rollback capability
- Index optimization
- Constraint validation
- Zero-downtime deployment