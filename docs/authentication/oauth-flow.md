# OAuth2 Authentication & Account Linking

SkillSwap Arena supports single-sign-on (SSO) and account linking with **Google** and **GitHub** OAuth2 providers.

---

## 1. OAuth Sequence Overview

```
[ User Browser ]                  [ FastAPI Backend ]              [ OAuth Provider (Google / GitHub) ]
       │                                   │                                         │
       │  1. GET /auth/oauth/authorize     │                                         │
       │     (?provider=google)            │                                         │
       │ ────────────────────────────────> │                                         │
       │                                   │  2. Generate state nonce & auth URL    │
       │  3. Redirect to Provider Auth URL │                                         │
       │ <──────────────────────────────── │                                         │
       │                                                                             │
       │  4. User consents & authorizes permissions                                  │
       │ ──────────────────────────────────────────────────────────────────────────> │
       │                                                                             │
       │  5. Redirects to /auth/callback?code=XYZ&state=ABC                          │
       │ <────────────────────────────────────────────────────────────────────────── │
       │                                   │                                         │
       │  6. POST /auth/oauth/callback     │                                         │
       │     ({ provider, code, state })   │                                         │
       │ ────────────────────────────────> │                                         │
       │                                   │  7. Exchange code for Access Token      │
       │                                   │ ──────────────────────────────────────> │
       │                                   │  8. Returns User Profile & Email        │
       │                                   │ <────────────────────────────────────── │
       │                                   │                                         │
       │                                   │  9. Lookup or Create User & Linked ID   │
       │                                   │  10. Generate SkillSwap JWT Token       │
       │  11. 200 OK (access_token, user)  │                                         │
       │ <──────────────────────────────── │                                         │
```

---

## 2. Account Linking & Collision Handling

When an OAuth callback arrives:
1. **Existing OAuth Link**: If `oauth_identities` matches `(provider, provider_user_id)`, the user is authenticated directly.
2. **Existing Email Match**: If a user exists with the same email (e.g. registered via email/password), the system securely links the OAuth identity to the existing account record without creating a duplicate user or duplicate wallet.
3. **New User**: If no match is found, a new user account is created with `role="USER"`, `is_active=True`, an initialized profile, and 5 welcome coins.

---

## 3. Security Controls
- **State Nonce Verification**: Protects against Cross-Site Request Forgery (CSRF) during the redirect phase.
- **Strict Callback Whitelisting**: Redirect URI is strictly validated against configured `FRONTEND_AUTH_CALLBACK_URL`.
- **Zero Token Leakage**: OAuth access tokens from Google/GitHub are used strictly for user profile retrieval and are never exposed to the client.
