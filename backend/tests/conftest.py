# conftest.py — project-wide pytest configuration for SkillSwap backend tests
# This file is intentionally minimal. Each test module manages its own
# SQLite in-memory engine and registers app.dependency_overrides[get_db]
# at import time. When running all tests together, the last-imported module's
# override is active for all subsequent tests.
#
# To work around this, each test module's autouse setup_db fixture now also
# re-registers the correct override for that module at fixture setup time and
# restores it (clears the override) at teardown time.
