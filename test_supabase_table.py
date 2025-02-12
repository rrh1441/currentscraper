from supabase import create_client
import os
from datetime import datetime

def test_supabase_table():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print("\nTesting Supabase Connection and Permissions")
    print("="*50)
    
    try:
        print("Initializing Supabase client...")
        supabase = create_client(url, key)
        
        # Test data with integer ID
        test_data = {
            'id': 999999,  # Using integer ID
            'name': 'Test Facility',
            'facility_type': 'Test Type',
            'address': 'Test Address',
            'available_times': 'Test Time',
            'last_updated': datetime.now().isoformat()
        }
        
        print("\nAttempting to write test data...")
        result = supabase.table("courts").upsert(test_data).execute()
        print("Write successful!")
        
        print("\nAttempting to read test data...")
        verification = supabase.table("courts").select("*").eq("id", 999999).execute()
        
        if verification.data:
            print("Read successful!")
            print("\nStored data:")
            print(verification.data[0])
        else:
            print("❌ No data found after write")
        
        print("\nAttempting to delete test data...")
        delete_result = supabase.table("courts").delete().eq("id", 999999).execute()
        print("Delete successful!")
        
        print("\n✅ All operations completed successfully!")
        
    except Exception as e:
        print("\n❌ Error during testing:")
        print(str(e))
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")

if __name__ == "__main__":
    test_supabase_table()