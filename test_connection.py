import os
from dotenv import load_dotenv
from supabase_py import create_client, Client

# Load the environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print("Testing Supabase connection...")
print(f"Supabase URL found: {'Yes' if supabase_url else 'No'}")
print(f"Supabase key found: {'Yes' if supabase_key else 'No'}")

try:
    # Initialize the client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Try a simple query
    response = supabase.table('courts').select("*").limit(1).execute()
    
    print("\nConnection successful!")
    print(f"Response data: {response}")
    
except Exception as e:
    print(f"\nError occurred: {str(e)}")
    print("\nPlease check your .env file contains:")
    print("SUPABASE_URL=your_project_url")
    print("SUPABASE_KEY=your_project_key")
