# from test_heatmap import (
    test_heatmap_unauthenticated_returns_401,
    test_heatmap_empty_user,
    test_heatmap_single_and_multiple_activities,
    test_heatmap_user_isolation,
    Base,
    engine
)

def run():
    print("Running heatmap test suite...")
    
    test_heatmap_unauthenticated_returns_401()
    print("✔ test_heatmap_unauthenticated_returns_401 PASSED")
    
    Base.metadata.create_all(bind=engine)
    try:
        test_heatmap_empty_user()
        print("✔ test_heatmap_empty_user PASSED")
    finally:
        Base.metadata.drop_all(bind=engine)
        
    Base.metadata.create_all(bind=engine)
    try:
        test_heatmap_single_and_multiple_activities()
        print("✔ test_heatmap_single_and_multiple_activities PASSED")
    finally:
        Base.metadata.drop_all(bind=engine)
        
    Base.metadata.create_all(bind=engine)
    try:
        test_heatmap_user_isolation()
        print("✔ test_heatmap_user_isolation PASSED")
    finally:
        Base.metadata.drop_all(bind=engine)

    print("\n==========================================")
    print("ALL HEATMAP TESTS COMPLETED & PASSED!")
    print("==========================================")

if __name__ == "__main__":
    run()
