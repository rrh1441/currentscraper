import socket
import requests
import dns.resolver
import subprocess
import platform
import os
from urllib.parse import urlparse
from datetime import datetime
import ssl
import json

def test_supabase_connectivity(supabase_url):
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    if not supabase_url:
        return {"error": "No Supabase URL provided"}
    
    # Parse the URL
    parsed_url = urlparse(supabase_url)
    hostname = parsed_url.hostname
    
    def run_test(name, func):
        try:
            result = func()
            results["tests"][name] = {"status": "success", "details": result}
        except Exception as e:
            results["tests"][name] = {"status": "failed", "error": str(e)}
    
    # Test 1: DNS Resolution
    def test_dns():
        # Try multiple DNS servers
        dns_servers = [
            ("Default", None),
            ("Google", "8.8.8.8"),
            ("Cloudflare", "1.1.1.1")
        ]
        
        dns_results = {}
        for server_name, server in dns_servers:
            try:
                if server:
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [server]
                    answers = resolver.resolve(hostname, 'A')
                else:
                    answers = dns.resolver.resolve(hostname, 'A')
                dns_results[server_name] = [str(rdata) for rdata in answers]
            except Exception as e:
                dns_results[server_name] = f"Failed: {str(e)}"
        return dns_results
    
    # Test 2: Direct Socket Connection
    def test_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, 443))
        sock.close()
        return {
            "port_443_open": result == 0,
            "error_code": result
        }
    
    # Test 3: HTTPS Request
    def test_https():
        response = requests.get(f"https://{hostname}/rest/v1/", timeout=5)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers)
        }
    
    # Test 4: SSL Certificate
    def test_ssl():
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            cert = s.getpeercert()
        return {
            "issuer": cert['issuer'],
            "subject": cert['subject'],
            "expires": cert['notAfter']
        }
    
    # Test 5: Ping
    def test_ping():
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "4", hostname]
        try:
            output = subprocess.check_output(command).decode().strip()
            return {"output": output}
        except subprocess.CalledProcessError as e:
            return {"error": str(e)}
    
    # Test 6: Traceroute
    def test_traceroute():
        if platform.system().lower() == "windows":
            command = ["tracert", hostname]
        else:
            command = ["traceroute", hostname]
        try:
            output = subprocess.check_output(command).decode().strip()
            return {"output": output}
        except subprocess.CalledProcessError as e:
            return {"error": str(e)}
        except FileNotFoundError:
            return {"error": "traceroute/tracert command not found"}
    
    # Run all tests
    run_test("dns_resolution", test_dns)
    run_test("socket_connection", test_socket)
    run_test("https_request", test_https)
    run_test("ssl_certificate", test_ssl)
    run_test("ping", test_ping)
    run_test("traceroute", test_traceroute)
    
    return results

def print_results(results):
    print("\n=== Supabase Connectivity Test Results ===")
    print(f"Timestamp: {results['timestamp']}\n")
    
    for test_name, test_data in results['tests'].items():
        print(f"=== {test_name.upper()} ===")
        if test_data['status'] == 'success':
            print("Status: ✅ Success")
            print("Details:")
            print(json.dumps(test_data['details'], indent=2))
        else:
            print("Status: ❌ Failed")
            print(f"Error: {test_data['error']}")
        print()

if __name__ == "__main__":
    # Get Supabase URL from environment variable or input
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        supabase_url = input("Enter your Supabase URL: ")
    
    results = test_supabase_connectivity(supabase_url)
    print_results(results)