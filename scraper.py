import os
import json
import scrapy
import socket
import dns.resolver
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
import time

# Load environment variables
load_dotenv()

# Set up Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

class AncSpider(scrapy.Spider):
    name = 'AncSpider'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,  # Increased delay
        'LOG_LEVEL': 'DEBUG',
        'HTTPCACHE_ENABLED': False,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 404, 403, 429],
        'DOWNLOAD_TIMEOUT': 60,  # Increased timeout
        'COOKIES_ENABLED': True,
        'COOKIES_DEBUG': True
    }

    def __init__(self, *args, **kwargs):
        super(AncSpider, self).__init__(*args, **kwargs)
        self.tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%m/%d/%Y")
        self.retry_delays = [5, 10, 30]
        self.session_valid = False
        
        # Resolve domain using multiple methods
        try:
            # Try default DNS
            self.resolved_ip = socket.gethostbyname('anc.apm.activecommunities.com')
            print(f"Resolved IP (default DNS): {self.resolved_ip}")
        except socket.gaierror:
            try:
                # Try Google DNS
                resolver = dns.resolver.Resolver()
                resolver.nameservers = ['8.8.8.8', '1.1.1.1']
                answers = resolver.resolve('anc.apm.activecommunities.com', 'A')
                self.resolved_ip = answers[0].address
                print(f"Resolved IP (Google DNS): {self.resolved_ip}")
            except Exception as e:
                # Fallback to known IP if everything fails
                self.resolved_ip = 'anc-ats-u1-vip.apm.activecommunities.com'
                print(f"Using fallback IP: {self.resolved_ip}")

        print(f"Spider initialized - searching for dates: {self.tomorrow}")

    def get_headers(self, csrf=None):
        """Centralized header management"""
        headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Host': 'anc.apm.activecommunities.com',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        if csrf:
            headers.update({
                'X-CSRF-Token': csrf,
                'X-Requested-With': 'XMLHttpRequest'
            })
        return headers

    def errback_httpbin(self, failure):
        request = failure.request
        if failure.check(DNSLookupError):
            print(f"DNS Lookup Error on {request.url}")
            # Use the pre-resolved IP
            new_url = request.url.replace('anc.apm.activecommunities.com', self.resolved_ip)
            print(f"Retrying with resolved IP: {new_url}")
            return request.replace(url=new_url)
        elif failure.check(TimeoutError):
            print(f"Timeout Error on {request.url}")
        elif failure.check(HttpError):
            response = failure.value.response
            print(f"HTTP Error {response.status} on {request.url}")
            if response.status == 403:
                self.session_valid = False
                # Restart the session
                return self.start_requests()
        
        retry_times = request.meta.get('retry_times', 0)
        if retry_times < len(self.retry_delays):
            delay = self.retry_delays[retry_times]
            print(f"Retrying request to {request.url} (attempt {retry_times + 1}) after {delay}s")
            time.sleep(delay)
            request.meta['retry_times'] = retry_times + 1
            return request

    def start_requests(self):
        print("\nStarting requests")
        urls = [
            f'https://{self.resolved_ip}/seattle/myaccount?onlineSiteId=0&from_original_cui=true&online=true&locale=en-US',
            'https://anc.apm.activecommunities.com/seattle/myaccount?onlineSiteId=0&from_original_cui=true&online=true&locale=en-US'
        ]
        
        for url in urls:
            yield scrapy.Request(
                url=url,
                headers=self.get_headers(),
                callback=self.parse,
                errback=self.errback_httpbin,
                dont_filter=True,
                meta={
                    'dont_retry': False,
                    'max_retry_times': 5,
                    'download_timeout': 60
                }
            )

    def parse(self, response):
        print("\nGetting CSRF token")
        csrf = response.xpath('//script/text()').re_first('window.__csrfToken = "(.*)";')
        if not csrf:
            print("No CSRF token found - retrying")
            return self.start_requests()
            
        print(f"CSRF Token: {csrf}")

        url = f'https://{self.resolved_ip}/seattle/rest/user/signin?locale=en-US'
        headers = self.get_headers(csrf)
        headers['Content-Type'] = 'application/json;charset=utf-8'

        payload = {
            "login_name": "Seattletennisguy@gmail.com",
            "password": "ThisIsMyPassword44",
            "signin_source_app": "0",
            "from_original_cui": "true",
            "onlineSiteId": "0"
        }

        print("\nAttempting login...")
        yield scrapy.Request(
            url=url,
            method='POST',
            headers=headers,
            body=json.dumps(payload),
            callback=self.after_login,
            errback=self.errback_httpbin,
            meta={'csrf': csrf},
            dont_filter=True
        )

    def after_login(self, response):
        try:
            print("\nProcessing login response")
            login_data = json.loads(response.text)
            if login_data.get('body', {}).get('result', {}).get('success'):
                print("Login successful")
                csrf = response.meta['csrf']
                self.session_valid = True
                
                url = f'https://{self.resolved_ip}/seattle/rest/reservation/resource?locale=en-US'
                headers = self.get_headers(csrf)
                headers['Content-Type'] = 'application/json;charset=utf-8'
                
                payload = {
                    "facility_type_ids": [39, 115],
                    "page_size": 100,
                    "start_index": 0
                }
                
                yield scrapy.Request(
                    url=url,
                    method='POST',
                    headers=headers,
                    body=json.dumps(payload),
                    callback=self.parse_facilities,
                    errback=self.errback_httpbin,
                    meta={'csrf': csrf},
                    dont_filter=True
                )
            else:
                print("Login failed")
                self.session_valid = False
        except Exception as e:
            print(f"Error in after_login: {str(e)}")
            self.session_valid = False

    def parse_facilities(self, response):
        try:
            print("\nParsing facilities")
            data = json.loads(response.text)
            facilities = data.get('body', {}).get('items', [])
            print(f"Found {len(facilities)} facilities")
            
            csrf = response.meta['csrf']
            
            for facility in facilities:
                try:
                    facility_id = facility.get('id')
                    timestamp = int(datetime.now().timestamp())
                    availability_url = (
                        f'https://{self.resolved_ip}/seattle/rest/reservation/resource/availability/daily/'
                        f'{facility_id}?start_date={self.tomorrow}&end_date={self.tomorrow}&attendee=1&_={timestamp}'
                    )
                    
                    print(f"\nChecking availability URL: {availability_url}")
                    
                    yield scrapy.Request(
                        url=availability_url,
                        callback=self.parse_availability,
                        errback=self.errback_httpbin,
                        meta={
                            'facility': {
                                'id': str(facility_id),
                                'name': facility.get('name', 'Unknown'),
                                'facility_type': facility.get('type_name', 'Unknown'),
                                'address': facility.get('center_name', 'Unknown')
                            }
                        },
                        headers=self.get_headers(csrf),
                        dont_filter=True
                    )
                except Exception as e:
                    print(f"Error processing facility {facility.get('name', 'Unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error in parse_facilities: {str(e)}")

    def parse_availability(self, response):
        facility = response.meta['facility']
        try:
            print(f"\n{'='*50}")
            print(f"Processing facility: {facility['name']}")
            
            data = json.loads(response.text)
            daily_details = data.get('body', {}).get('details', {}).get('daily_details', [])
            
            available_times = []
            for day in daily_details:
                date_str = day.get('date')
                try:
                    api_date = datetime.strptime(date_str, "%m/%d/%Y")
                    target_date = datetime.strptime(self.tomorrow, "%m/%d/%Y")
                    
                    if api_date == target_date:
                        for time_slot in day.get('times', []):
                            if time_slot.get('available'):
                                time_str = f"{date_str} {time_slot.get('start_time')}-{time_slot.get('end_time')}"
                                available_times.append(time_str)
                                print(f"Found available time: {time_str}")
                except ValueError as e:
                    print(f"Date parsing error: {str(e)}")
                    continue
            
            # Convert ID to integer
            try:
                facility_id = int(facility['id'])
            except ValueError:
                print(f"Warning: Invalid facility ID format: {facility['id']}")
                facility_id = hash(facility['id']) % 1000000  # Fallback to hash if can't convert
            
            facility_data = {
                'id': facility_id,  # Using integer ID
                'name': facility['name'],
                'facility_type': facility['facility_type'],
                'address': facility['address'],
                'available_times': '\n'.join(available_times) if available_times else '',
                'last_updated': datetime.now().isoformat()
            }
            
            print("\nPrepared data for Supabase:")
            print(json.dumps(facility_data, indent=2))
            
            try:
                print("\nAttempting to write to Supabase...")
                result = self.supabase_manager.client.table("courts").upsert(facility_data).execute()
                
                print("\nVerifying write operation...")
                verification = self.supabase_manager.client.table("courts") \
                    .select("*") \
                    .eq("id", facility_id) \
                    .execute()
                
                if verification.data:
                    print(f"✅ Successfully verified data for {facility['name']}")
                    print("Stored data:")
                    print(json.dumps(verification.data[0], indent=2))
                else:
                    print(f"❌ Data verification failed for {facility['name']}")
                    print("No data found after write operation")
                
            except Exception as e:
                print(f"\n❌ Supabase error for {facility['name']}: {str(e)}")
                print("Error details:")
                if hasattr(e, 'response'):
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response body: {e.response.text}")
                raise e
                
        except Exception as e:
            print(f"\n❌ Error processing facility {facility['name']}: {str(e)}")
            print(f"{'='*50}\n")