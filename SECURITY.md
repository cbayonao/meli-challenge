# 🔒 Security Guidelines for Meli Challenge

## ⚠️ IMPORTANT: Never commit sensitive information to version control!

This document outlines security best practices for the Meli Challenge project.

## 🚨 Critical Security Rules

### 1. **NEVER commit these to Git:**
- API Keys (Zyte, OpenAI, AWS)
- AWS Access Keys and Secret Keys
- Database credentials
- Private URLs or endpoints
- Personal information
- Environment files (.env)

### 2. **Always use environment variables:**
```bash
# ✅ CORRECT - Use environment variables
ZYTE_API_KEY=${env:ZYTE_API_KEY}
OPENAI_API_KEY=${env:OPENAI_API_KEY}

# ❌ WRONG - Hardcoded values
ZYTE_API_KEY=XXXXXX
OPENAI_API_KEY=xxxxxxGT3BlbkFJZcPfcwh2PV_uITHcygqDA1zgRQLTJG0TIDfLMy8zUiGkTaKbH9mDwmQGDK1f21zor5iJgyKIsA
```

## 🛡️ Security Best Practices

### Environment Variables
1. **Create `.env` file locally** (never commit this)
2. **Use `env.example`** for documentation
3. **Set variables in CI/CD** securely
4. **Rotate keys regularly**

### AWS Security
1. **Use IAM roles** instead of access keys when possible
2. **Principle of least privilege** for permissions
3. **Enable CloudTrail** for audit logging
4. **Use AWS Secrets Manager** for sensitive data

### Code Security
1. **Input validation** for all user inputs
2. **Output encoding** to prevent XSS
3. **Regular dependency updates** to patch vulnerabilities
4. **Code reviews** for security issues

## 🔍 Security Checklist

Before committing code, ensure:

- [ ] No API keys in code
- [ ] No hardcoded credentials
- [ ] No sensitive URLs
- [ ] Environment variables used correctly
- [ ] `.env` file in `.gitignore`
- [ ] No debug information exposed
- [ ] Proper error handling (no stack traces in production)

## 🚨 If you accidentally commit sensitive data:

1. **Immediately revoke** the exposed credentials
2. **Generate new credentials**
3. **Update all environments** with new values
4. **Remove from Git history** using `git filter-branch` or BFG
5. **Force push** to remove from remote repository
6. **Notify team members** to update their local copies

## 📚 Resources

- [GitHub Security Best Practices](https://docs.github.com/en/github/security)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-learning/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

## 🆘 Security Contact

If you discover a security vulnerability:
1. **DO NOT** create a public issue
2. **Contact** the project maintainers privately
3. **Provide** detailed information about the vulnerability
4. **Wait** for response before public disclosure

---

**Remember: Security is everyone's responsibility!** 🔒
