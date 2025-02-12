import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def print_court_details(court):
    print("\n" + "="*70)
    print(f"ID: {court.get('id')}")
    print(f"Name: {court.get('name')}")
    print(f"Facility Type: {court.get('facility_type')}")
    print(f"Address: {court.get('address')}")
    print(f"Last Updated: {court.get('last_updated', 'Not available')}")
    print("\nAvailable Times:")
    times = court.get('available_times', '').split('\n')
    for time in times:
        if time.strip():
            print(f"  - {time.strip()}")
    print("="*70)

def main():
    print("Checking court data...")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tomorrow's date should be: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}")

    try:
        # Query all courts
        response = supabase.table("courts").select("*").execute()
        courts = response.data
        
        print(f"\nTotal courts found: {len(courts)}")
        
        # Sort courts by last_updated if it exists
        if courts and 'last_updated' in courts[0]:
            courts.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        
        print("\nMost recent entries:")
        
        # Display the first 5 entries with detailed information
        for court in courts[:5]:
            print_court_details(court)

        # Count courts by facility type
        facility_types = {}
        for court in courts:
            ftype = court.get('facility_type', 'Unknown')
            facility_types[ftype] = facility_types.get(ftype, 0) + 1
        
        print("\nCourts by facility type:")
        for ftype, count in facility_types.items():
            print(f"{ftype}: {count} courts")

    except Exception as e:
        print(f"Error querying data: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
