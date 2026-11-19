## Description
Briefly describe the proposed changes, the motivations behind them, and what problem they resolve.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing features to break)
- [ ] Security / Performance enhancement

## Security Checklist
- [ ] No secrets, keys, or passwords are hardcoded in code or history.
- [ ] All inputs are validated on the server side; no SQL injection or XSS risks.
- [ ] Role-based access control (RBAC) and IDOR checks are strictly enforced.
- [ ] Database queries are optimized with appropriate indexes and atomic transactions.
- [ ] All automated tests pass (`python manage.py test`).
- [ ] New endpoints have appropriate rate limiting or permissions.

## Testing Performed
Describe unit/integration tests added or manual verification conducted.
