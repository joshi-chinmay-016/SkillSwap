# Nginx Networking & Reverse Proxy

SkillSwap Arena employs **Nginx** as both the internal static SPA web server and the production reverse proxy gateway (`docker/production/nginx.conf`).

---

## 1. Gateway Responsibilities

1. **WebSocket Upgrade & Long-Lived Timeouts**:
   ```nginx
   location /ws/ {
       proxy_pass http://backend_pool/ws/;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "Upgrade";
       proxy_read_timeout 3600s;
       proxy_send_timeout 3600s;
   }
   ```
2. **Strict Security Headers**:
   - `X-Frame-Options: DENY` (prevents clickjacking)
   - `X-Content-Type-Options: nosniff` (prevents MIME sniffing)
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-XSS-Protection: 1; mode=block`
3. **Structured JSON Access Logging**:
   Emits machine-parsable JSON logs with `request_id`, `client_ip`, `status`, `request_time`, and `upstream_response_time`.
4. **Rate Limiting Zones**:
   - `auth_limit`: 10 requests/sec on `/auth/*`.
   - `api_limit`: 30 requests/sec on `/api/*`.
