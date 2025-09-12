---
description: Create new API endpoint
argument-hint: [method path, e.g., GET /users]
---

Create new API endpoint: $ARGUMENTS

1. Define route handler with proper HTTP method
2. Create request/response models (DTOs)
3. Implement input validation
4. Add business logic in service layer
5. Implement data access in repository
6. Add error handling and logging
7. Write unit and integration tests
8. Update OpenAPI documentation
9. Add rate limiting if needed

Endpoint should include:
- Proper HTTP status codes
- Request validation
- Error responses
- Pagination (if list endpoint)
- Authentication/authorization
- Response caching (if applicable)