"""
SkillSwap Arena — Automated Screenshot Capture Script (Phase 8.10)
Uses Playwright to capture real application screenshots from running frontend and backend.
"""
import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../docs/screenshots"))
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Login Page
        print("Capturing login.png...")
        page.goto("http://localhost:5173/login", wait_until="networkidle")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "login.png"))

        # Perform Login as Admin
        page.fill('input[type="email"]', "admin@skillswap.local")
        page.fill('input[type="password"]', "AdminSecurePass123!")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        # 2. Student Dashboard
        print("Capturing dashboard.png...")
        page.goto("http://localhost:5173/dashboard", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "dashboard.png"))

        # 3. Mentor Discovery
        print("Capturing mentor-discovery.png...")
        page.goto("http://localhost:5173/mentors", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mentor-discovery.png"))

        # 4. Peer Sessions
        print("Capturing session.png...")
        page.goto("http://localhost:5173/sessions", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "session.png"))

        # 5. Learning Journey & Roadmap
        print("Capturing learning-journey.png...")
        page.goto("http://localhost:5173/journey/roadmap", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "learning-journey.png"))

        # 6. AI Session Intelligence / AIMentor
        print("Capturing session-intelligence.png...")
        page.goto("http://localhost:5173/mentor", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "session-intelligence.png"))

        # 7. Admin Dashboard
        print("Capturing admin-dashboard.png...")
        page.goto("http://localhost:5173/admin", wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "admin-dashboard.png"))

        # 8. Admin Users
        print("Capturing admin-users.png...")
        page.goto("http://localhost:5173/admin/users", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "admin-users.png"))

        # 9. Admin Analytics
        print("Capturing admin-analytics.png...")
        page.goto("http://localhost:5173/admin/analytics", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "admin-analytics.png"))

        # 10. System Health / Diagnostics
        print("Capturing system-monitoring.png...")
        page.goto("http://localhost:5173/admin/system", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "system-monitoring.png"))

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture_all()
