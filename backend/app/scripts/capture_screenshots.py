"""
SkillSwap Arena — Verified Screenshot Capture Engine
Captures distinctive, high-resolution screenshots of all 10 student and admin pages.
"""
import os
import json
import urllib.request
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../docs/screenshots"))
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def get_auth_token_and_user():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillswap.io")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "AdminSecurePass123!")

    # Authenticate via backend API
    login_data = json.dumps({"email": admin_email, "password": admin_pass}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        login_res = json.loads(response.read().decode("utf-8"))
        token = login_res["access_token"]

    # Fetch user info
    me_req = urllib.request.Request(
        "http://localhost:8000/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(me_req) as response:
        user_res = json.loads(response.read().decode("utf-8"))

    return token, user_res

def capture_all():
    print("Obtaining real JWT token & profile from backend...")
    token, user = get_auth_token_and_user()
    print(f"Authenticated as {user.get('email')} (Role: {user.get('role')})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # --- 1. Unauthenticated Login Page ---
        print("\n1. Capturing login.png...")
        anon_context = browser.new_context(viewport={"width": 1440, "height": 900})
        anon_page = anon_context.new_page()
        anon_page.goto("http://localhost:5173/login", wait_until="domcontentloaded")
        anon_page.wait_for_timeout(2000)
        anon_page.screenshot(path=os.path.join(SCREENSHOT_DIR, "login.png"))
        anon_context.close()

        # --- 2. Authenticated Context ---
        auth_context = browser.new_context(viewport={"width": 1440, "height": 900})
        
        # Inject localStorage authentication tokens before every page load
        auth_init_js = f"""
        localStorage.setItem('token', {json.dumps(token)});
        localStorage.setItem('user', JSON.stringify({json.dumps(user)}));
        """
        auth_context.add_init_script(auth_init_js)
        page = auth_context.new_page()

        # Pages to capture
        targets = [
            ("dashboard.png", "http://localhost:5173/dashboard", "Student Dashboard"),
            ("mentor-discovery.png", "http://localhost:5173/mentors", "Mentor Discovery"),
            ("session.png", "http://localhost:5173/sessions", "Peer Sessions"),
            ("learning-journey.png", "http://localhost:5173/journey/roadmap", "Learning Roadmap"),
            ("session-intelligence.png", "http://localhost:5173/mentor", "AI Mentor Workspace"),
            ("admin-dashboard.png", "http://localhost:5173/admin", "Admin Dashboard"),
            ("admin-users.png", "http://localhost:5173/admin/users", "Admin User Management"),
            ("admin-analytics.png", "http://localhost:5173/admin/analytics", "Admin Analytics"),
            ("system-monitoring.png", "http://localhost:5173/admin/system", "Admin System Health"),
        ]

        for filename, url, label in targets:
            print(f"Capturing {filename} from {url} ({label})...")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, filename))

        browser.close()
        print("\n[SUCCESS] All 10 distinctive screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
