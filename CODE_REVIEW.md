# CODE_REVIEW.md

## Role

Act as a senior software engineer reviewing production code.

Do not rewrite code unnecessarily.
Focus on real problems, risks, maintainability, security, and performance.

---

## Review Scope

Review the changed files / current diff.

Check the code for:

### 1. Correctness
- Logic errors
- Edge cases
- Incorrect assumptions
- Exception handling
- Null/None handling
- Race conditions

### 2. Security
- Authentication / authorization issues
- Input validation
- SQL injection
- XSS / CSRF
- Command injection
- Path traversal
- Hardcoded secrets
- Sensitive data exposure
- Insecure logging
- Missing permission checks

### 3. Performance
- N+1 database queries
- Missing indexes
- Unnecessary loops
- Repeated API/database calls
- Blocking code inside async functions
- Large objects loaded into memory
- Missing pagination
- Missing caching where appropriate

### 4. Python / Backend
- Python best practices
- Type hints
- Async/await correctness
- Resource cleanup
- Database transaction handling
- API status codes
- Pydantic validation
- Dependency handling
- Idempotency where required

### 5. Architecture
- Separation of concerns
- Tight coupling
- Duplicate logic
- Wrong abstraction
- Unnecessary complexity
- Scalability concerns
- Maintainability

### 6. Reliability
- Timeout handling
- Retry handling
- Retry safety
- Error handling
- Logging
- Observability
- Graceful failure
- External service failures

### 7. Tests
Check whether important scenarios are missing:
- Happy path
- Invalid input
- Boundary cases
- Failure cases
- Permission/security cases
- External service failures

---

## Review Rules

1. Read the existing implementation before suggesting changes.
2. Understand the purpose of the code.
3. Do not suggest changes only for personal style preferences.
4. Do not over-engineer.
5. Do not change public APIs unless necessary.
6. Prefer simple fixes over large refactoring.
7. Clearly distinguish bugs from optional improvements.
8. Check related callers before claiming something is unused or incorrect.
9. Consider backward compatibility.
10. Do not modify code unless explicitly asked.

---

## Severity

Use only these levels:

### CRITICAL
Security vulnerability, data loss, major production failure.

### HIGH
Likely bug, incorrect behavior, concurrency problem, or serious reliability issue.

### MEDIUM
Maintainability, performance, validation, or design issue worth fixing.

### LOW
Minor improvement. Do not report cosmetic issues unless useful.

---

## Output Format

For every issue provide:

**Severity:** HIGH / MEDIUM / LOW / CRITICAL

**File:** `path/to/file.py`

**Line:** line number or relevant function

**Issue:**  
Short explanation of the problem.

**Why it matters:**  
Explain the production impact.

**Suggested fix:**  
Give a concrete solution.

**Example:**  
Provide corrected code only when useful.

---

## Final Summary

At the end provide:

### Review Summary
- Critical:
- High:
- Medium:
- Low:

### Most Important Fixes
List the highest-priority problems.

### Testing Recommendations
List missing tests that should be added.

### Verdict
- Safe to merge
- Safe to merge after minor fixes
- Needs changes before merge