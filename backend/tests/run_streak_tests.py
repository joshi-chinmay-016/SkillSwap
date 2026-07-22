from tests.test_streak import (
    test_streak_unauthenticated_returns_401,
    test_streak_empty_user,
    test_streak_single_active_day_today,
    test_streak_active_yesterday_not_today,
    test_streak_consecutive_days_and_longest,
    test_streak_broken_streak,
    test_streak_multiple_activities_same_day,
    test_streak_user_isolation,
    test_streak_read_only_integrity,
    setup_db
)

def run_all_streak_tests():
    print("==========================================")
    print("RUNNING LEARNING STREAK TEST SUITE")
    print("==========================================")

    tests = [
        ("test_streak_unauthenticated_returns_401", test_streak_unauthenticated_returns_401),
        ("test_streak_empty_user", test_streak_empty_user),
        ("test_streak_single_active_day_today", test_streak_single_active_day_today),
        ("test_streak_active_yesterday_not_today", test_streak_active_yesterday_not_today),
        ("test_streak_consecutive_days_and_longest", test_streak_consecutive_days_and_longest),
        ("test_streak_broken_streak", test_streak_broken_streak),
        ("test_streak_multiple_activities_same_day", test_streak_multiple_activities_same_day),
        ("test_streak_user_isolation", test_streak_user_isolation),
        ("test_streak_read_only_integrity", test_streak_read_only_integrity),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        db_gen = setup_db()
        next(db_gen)
        try:
            test_fn()
            print(f"✔ {name} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    print("==========================================")
    print(f"RESULTS: {passed} PASSED, {failed} FAILED")
    print("==========================================")
    if failed > 0:
        raise RuntimeError(f"{failed} tests failed.")

if __name__ == "__main__":
    run_all_streak_tests()
