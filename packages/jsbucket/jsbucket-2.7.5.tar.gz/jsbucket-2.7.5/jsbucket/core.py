import argparse
import requests
from urllib.parse import urljoin
import re
import json
import threading
from tqdm import tqdm
from rich.console import Console
from rich.style import Style
import os
import tldextract
from typing import List, Dict, Optional, Any
import time
from datetime import datetime
import pickle
import queue
import concurrent.futures

# force ANSI support on Windows
os.system("")

# Default console instance for CLI usage
_console = Console(force_terminal=True)

# ProjectDiscovery-style colors
info_style = Style(color="cyan", bold=True)        # [INF]
warn_style = Style(color="yellow", bold=True)      # [WRN]
error_style = Style(color="red", bold=True)        # [ERR]
success_style = Style(color="green", bold=True)    # [SUC]
highlight_style = Style(color="bright_white", bold=True)  # Important text
normal_style = Style(color="white")                # Normal text
dim_style = Style(color="bright_black")           # Secondary text

# Legacy styles for backward compatibility (gradually phase out)
json_key_style = Style(color="green", bold=True)  
subdomain_value_style = Style(color="blue")  
bucket_name_value_style = Style(color="cyan") 
bucket_url_value_style = Style(color="blue") 
progress_style = Style(color="magenta", bold=True) 

def print_banner():
    """Print JSBucket ASCII banner."""
    banner = """
   _     _                _        _   
  (_)___| |__  _   _  ___| | _____| |_ 
  | / __| '_ \| | | |/ __| |/ / _ \ __|
  | \__ \ |_) | |_| | (__|   <  __/ |_ 
 _/ |___/_.__/ \__,_|\___|_|\_\___|\__|
|__/           @saeed0x1
    """
    _console.print(banner, style=highlight_style)

def log_info(message: str):
    """Print info message with [INF] tag."""
    _console.print(f"[INF] {message}", style=info_style)

def log_warn(message: str):
    """Print warning message with [WRN] tag.""" 
    _console.print(f"[WRN] {message}", style=warn_style)

def log_error(message: str):
    """Print error message with [ERR] tag."""
    _console.print(f"[ERR] {message}", style=error_style)

def log_success(message: str):
    """Print success message with [SUC] tag."""
    _console.print(f"[SUC] {message}", style=success_style) 

# Progress tracking functions (streaming-based approach)
def save_progress(info_file: str, session_data: Dict[str, Any]) -> None:
    """Save minimal progress data to info file."""
    try:
        with open(info_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        log_warn(f"Could not save progress: {e}")

def load_progress(info_file: str) -> Optional[Dict[str, Any]]:
    """Load progress from info file."""
    try:
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_warn(f"Could not load progress file: {e}")
    return None

def create_session_data(input_file: str, total_lines: int, args: argparse.Namespace) -> Dict[str, Any]:
    """Create minimal session data structure with position-based tracking."""
    return {
        'start_time': datetime.now().isoformat(),
        'input_file': input_file,  # Store source file path
        'total_subdomains': total_lines,
        'current_position': 0,  # Line number in file (0-based)
        'completed_count': 0,
        'last_processed_subdomain': None,  # Track last subdomain for verification
        'results_with_buckets': [],  # Only store results that found buckets
        'args': {
            'timeout': args.timeout,
            'threads': args.threads,
            'domain': args.domain,
            'output': args.output,
            'silent': args.silent,
            'header': getattr(args, 'header', None)
        },
        'version': '2.6.1',
        'save_interval': 100  # Save progress every N completions
    }

def update_session_progress(session_data: Dict[str, Any], line_number: int, subdomain: str, result: Dict[str, Any]) -> None:
    """Update session progress with position tracking."""
    session_data['current_position'] = line_number
    session_data['completed_count'] += 1
    session_data['last_processed_subdomain'] = subdomain
    
    # Only store results with S3 buckets found
    if result.get('s3_buckets'):
        session_data['results_with_buckets'].append(result)
    
    session_data['last_update'] = datetime.now().isoformat()

def should_save_progress(session_data: Dict[str, Any]) -> bool:
    """Determine if progress should be saved based on interval."""
    return session_data['completed_count'] % session_data['save_interval'] == 0

def count_file_lines(filepath: str) -> int:
    """Efficiently count lines in a file without loading it into memory."""
    try:
        with open(filepath, 'r') as f:
            return sum(1 for _ in f)
    except:
        return 0

def parse_headers(header_list: Optional[List[str]]) -> Dict[str, str]:
    """
    Parse custom headers from command line arguments.
    
    Args:
        header_list: List of header strings in format "Header: value"
        
    Returns:
        Dictionary of parsed headers
        
    Examples:
        >>> parse_headers(["Cookie: session=abc123", "Authorization: Bearer token"])
        {"Cookie": "session=abc123", "Authorization": "Bearer token"}
    """
    headers = {}
    if header_list:
        for header in header_list:
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            else:
                log_warn(f"Invalid header format (missing ':'): {header}")
    return headers

def stream_subdomains_from_file(filepath: str, start_position: int = 0):
    """Generator that streams subdomains from file starting at given position."""
    try:
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                if i < start_position:
                    continue
                subdomain = line.strip()
                if subdomain:
                    yield i, subdomain
    except FileNotFoundError:
        raise FileNotFoundError(f"Subdomain file not found: {filepath}")

class SubdomainWorker:
    """Worker class for processing subdomains with bounded concurrency."""
    
    def __init__(self, args, session_data=None, info_file=None, lock=None):
        self.args = args
        self.session_data = session_data
        self.info_file = info_file 
        self.lock = lock

    def process_subdomain(self, line_data):
        """Process a single subdomain and return result."""
        line_number, subdomain = line_data
        
        # Parse headers from args if available
        headers = parse_headers(getattr(self.args, 'header', None))
        
        # Analyze the subdomain
        result = analyze_subdomain_for_s3_buckets(subdomain, self.args.timeout, headers=headers)
        
        # Display results if found and not silent
        if result["s3_buckets"] and not self.args.silent:
            # Clean ProjectDiscovery-style output using tqdm.write to avoid progress bar conflicts
            from tqdm import tqdm
            for bucket in result["s3_buckets"]:
                # Format: [FOUND] [STATUS] [bucket.s3.amazonaws.com] [subdomain]
                # Use simple ANSI colors that work with tqdm.write()
                green = "\033[92m"    # Green for [FOUND]
                white = "\033[97m"    # Bright white for bucket URL
                red = "\033[91m"      # Red for forbidden/error
                yellow = "\033[93m"   # Yellow for redirects/warnings  
                cyan = "\033[96m"     # Cyan for status
                normal = "\033[0m"    # Reset color
                
                found_part = f"{green}[FOUND]{normal}"
                
                # Color status based on accessibility
                status_text = bucket.get('status_text', 'UNKNOWN')
                if bucket.get('accessible', False):
                    if status_text == 'PUBLIC':
                        status_part = f"{green}[{status_text}]{normal}"
                    else:
                        status_part = f"{yellow}[{status_text}]{normal}"
                else:
                    status_part = f"{red}[{status_text}]{normal}"
                
                bucket_url_part = f"{white}[{bucket['bucket_url']}]{normal}"
                subdomain_part = f"{cyan}[{result['subdomain']}]{normal}"
                
                output = f"{found_part} {status_part} {bucket_url_part} {subdomain_part}"
                tqdm.write(output)
        
        # Thread-safe progress update
        if self.session_data and self.info_file and self.lock:
            with self.lock:
                update_session_progress(self.session_data, line_number, subdomain, result)
                if should_save_progress(self.session_data):
                    save_progress(self.info_file, self.session_data)
        
        return result

# fetch HTML content
def get_html_content(url: str, timeout: int = 20, verify: bool = True, headers: Optional[Dict[str, str]] = None) -> Optional[bytes]:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds
        verify: Whether to verify SSL certificates
        headers: Optional custom headers to include in the request
        
    Returns:
        HTML content as bytes, or None if request fails
    """
    try:
        response = requests.get(url, timeout=timeout, verify=verify, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        return None

# extract JavaScript URLs
def extract_js_urls(html_content: bytes, base_url: str, console: Optional[Console] = None) -> List[str]:
    """
    Extract JavaScript URLs from HTML content.
    
    Args:
        html_content: HTML content as bytes
        base_url: Base URL to resolve relative URLs
        console: Rich console instance for error output (optional)
        
    Returns:
        List of JavaScript URLs
    """
    try:
        js_urls = re.findall(r"(?<=src=['\"])[a-zA-Z0-9_\.\-\:\/]+\.js", html_content.decode('utf-8', 'ignore'))
        return [urljoin(base_url, js_url) for js_url in js_urls]
    except Exception as e:
        if console:
            console.print(f"Error extracting JavaScript URLs: {e}", style=error_style)
        return []

# extract S3 buckets
def extract_s3_buckets(content: Optional[bytes], console: Optional[Console] = None) -> List[str]:
    """
    Extract S3 bucket names from content.
    
    Args:
        content: Content to search for S3 bucket references
        console: Rich console instance for error output (optional)
        
    Returns:
        List of unique S3 bucket names
    """
    try:
        if content is None:
            return []

        # extract S3 bucket names
        decoded_content = content.decode('utf-8', 'ignore')
        regs3 = r"([\w\-\.]+)\.s3\.?(?:[\w\-\.]+)?\.amazonaws\.com|(?<!\.)s3\.?(?:[\w\-\.]+)?\.amazonaws\.com\\?\/([\w\-\.]+)"
        matches = re.findall(regs3, decoded_content)
        # filtering empty
        s3_buckets = [match[0] or match[1] for match in matches if match[0] or match[1]]
        # deduplicate
        return list(set(s3_buckets))
    except Exception as e:
        if console:
            console.print(f"Error extracting S3 Buckets: {e}", style=error_style)
        return []

# format JSON output
def format_json_with_colors(data: Dict[str, Any], console: Console) -> str:
    """
    Format JSON data with colors for terminal output.
    
    Args:
        data: Dictionary containing subdomain and S3 bucket data
        console: Rich console instance for rendering colors
        
    Returns:
        Formatted JSON string with colors
    """
    formatted_output = []
    for key, value in data.items():
        if key == "subdomain":
            formatted_output.append(
                f"{console.render_str(key, style=json_key_style)}: {console.render_str(value if value.startswith(('http://', 'https://')) else 'https://' + value, style=subdomain_value_style)}"
            )
        elif key == "s3_buckets": 
            formatted_buckets = "[\n"
            for bucket in value:
                bucket_formatted = []
                for k, v in bucket.items():
                    if k == 'bucket_name':
                        style = bucket_name_value_style
                    elif k == 'bucket_url':
                        style = bucket_url_value_style
                    elif k == 'status_code':
                        # Color based on status code
                        if v == 200:
                            style = "bright_green"
                        elif v == 403:
                            style = "red"
                        else:
                            style = "yellow"
                    elif k == 'status_text':
                        # Color based on status text
                        if 'PUBLIC' in str(v).upper():
                            style = "bright_green"
                        elif 'FORBIDDEN' in str(v).upper() or 'ERROR' in str(v).upper():
                            style = "red"
                        else:
                            style = "yellow"
                    elif k == 'accessible':
                        # Color based on accessibility
                        style = "bright_green" if v else "red"
                    else:
                        style = subdomain_value_style
                    
                    bucket_formatted.append(
                        f"    {console.render_str(k, style=json_key_style)}: "
                        f"{console.render_str(str(v), style=style)}"
                    )
                
                formatted_buckets += f"  {{\n{','.join(bucket_formatted)}\n  }},\n"
            formatted_buckets = formatted_buckets.rstrip(",\n") + "\n]"
            formatted_output.append(f"{console.render_str(key, style=json_key_style)}: {formatted_buckets}")
        elif key == "success":
            # Skip the success field in CLI display - it's only for API use
            continue
        else: 
            # Handle any other fields (convert to string first)
            formatted_output.append(
                f"{console.render_str(key, style=json_key_style)}: {console.render_str(str(value), style=subdomain_value_style)}"
            )
    return "{\n" + ",\n".join(formatted_output) + "\n}"

def extract_base_domain(subdomain: str) -> str:
    """
    Extract the base domain from a subdomain using tldextract.
    
    Args:
        subdomain: The subdomain to extract base domain from
        
    Returns:
        The extracted base domain
        
    Examples:
        >>> extract_base_domain('api.example.com')
        'example.com'
        >>> extract_base_domain('sub.api.example.com')
        'example.com'
        >>> extract_base_domain('https://www.example.co.uk')
        'example.co.uk'
        >>> extract_base_domain('test.example.com.au')
        'example.com.au'
    """
    # Remove protocol if present
    if subdomain.startswith(('http://', 'https://')):
        subdomain = subdomain.split('://', 1)[1]
    
    # Remove path if present
    if '/' in subdomain:
        subdomain = subdomain.split('/')[0]
    
    # Remove port if present
    if ':' in subdomain:
        subdomain = subdomain.split(':')[0]
    
    # Check if it's an IP address (return as-is)
    import ipaddress
    try:
        ipaddress.ip_address(subdomain)
        return subdomain  # Return IP address as-is
    except ValueError:
        pass  # Not an IP address, continue with domain processing
    
    # Use tldextract to properly parse the domain
    extracted = tldextract.extract(subdomain)
    
    # Combine domain + suffix to get the base domain
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    else:
        # Fallback to original subdomain if extraction fails
        return subdomain

def auto_detect_base_domain(subdomains: List[str]) -> Optional[str]:
    """
    Automatically detect the most common base domain from a list of subdomains.
    
    Args:
        subdomains: List of subdomains to analyze
        
    Returns:
        The most common base domain, or None if no common domain found
        
    Examples:
        >>> auto_detect_base_domain(['api.example.com', 'www.example.com', 'cdn.example.com'])
        'example.com'
    """
    if not subdomains:
        return None
    
    domain_counts = {}
    for subdomain in subdomains:
        base_domain = extract_base_domain(subdomain)
        domain_counts[base_domain] = domain_counts.get(base_domain, 0) + 1
    
    # Return the most common base domain
    if domain_counts:
        return max(domain_counts, key=domain_counts.get)
    
    return None

def check_s3_bucket_access(bucket_url: str, timeout: int = 10, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Check S3 bucket accessibility and return status information.
    
    Args:
        bucket_url: The S3 bucket URL to check
        timeout: Request timeout in seconds
        headers: Optional custom headers to include in the request
        
    Returns:
        Dictionary containing status_code, status_text, and accessible flag
    """
    try:
        response = requests.head(bucket_url, timeout=timeout, verify=True, allow_redirects=True, headers=headers)
        status_code = response.status_code
        
        # Determine accessibility and status text
        if status_code == 200:
            status_text = "PUBLIC"
            accessible = True
        elif status_code == 403:
            status_text = "FORBIDDEN"
            accessible = False
        elif status_code == 404:
            status_text = "NOT_FOUND"
            accessible = False
        elif status_code in [301, 302, 307, 308]:
            status_text = "REDIRECTED"
            accessible = True  # May be accessible after redirect
        else:
            status_text = f"HTTP_{status_code}"
            accessible = False
            
        return {
            "status_code": status_code,
            "status_text": status_text,
            "accessible": accessible
        }
    except requests.exceptions.Timeout:
        return {
            "status_code": 0,
            "status_text": "TIMEOUT",
            "accessible": False
        }
    except requests.exceptions.RequestException:
        return {
            "status_code": 0,
            "status_text": "ERROR",
            "accessible": False
        }

# Core API function for package users
def analyze_subdomain_for_s3_buckets(subdomain: str, timeout: int = 10, protocols: List[str] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze a single subdomain for S3 bucket references.
    
    This is the main API function for package users who want to programmatically
    analyze subdomains without CLI overhead.
    
    Args:
        subdomain: The subdomain to analyze (with or without protocol)
        timeout: Request timeout in seconds
        protocols: List of protocols to try (defaults to ['https://', 'http://'])
        headers: Optional custom headers to include in requests
        
    Returns:
        Dictionary containing:
        - subdomain: The analyzed subdomain with protocol
        - s3_buckets: List of dictionaries with bucket_name and bucket_url
        - success: Boolean indicating if analysis was successful
        
    Example:
        >>> result = analyze_subdomain_for_s3_buckets('example.com')
        >>> print(result['s3_buckets'])
        [{'bucket_name': 'my-bucket', 'bucket_url': 'https://my-bucket.s3.amazonaws.com'}]
    """
    if protocols is None:
        protocols = ["https://", "http://"]
    
    result_entry = {"subdomain": subdomain, "s3_buckets": [], "success": False}
    
    successful_protocol = None
    html_content = None
    
    # Handle subdomains that already have a protocol
    if any(subdomain.startswith(protocol) for protocol in protocols):
        full_url = subdomain
        try:
            response = requests.get(full_url, timeout=timeout, verify=True, headers=headers)
            response.raise_for_status()
            html_content = response.content
            successful_protocol = full_url.split("://")[0] + "://"
        except requests.exceptions.RequestException:
            pass
    else:
        # Try each protocol in order
        for protocol in protocols:
            full_url = f"{protocol}{subdomain}"
            try:
                response = requests.get(full_url, timeout=timeout, verify=True, headers=headers)
                response.raise_for_status()
                html_content = response.content
                successful_protocol = protocol
                break
            except requests.exceptions.RequestException:
                continue
    
    if not successful_protocol or html_content is None:
        return result_entry
    
    # Update subdomain with successful protocol
    subdomain_with_protocol = (f"{successful_protocol}{subdomain}" 
                              if not subdomain.startswith(('http://', 'https://')) 
                              else subdomain)
    result_entry["subdomain"] = subdomain_with_protocol
    
    try:
        # Extract S3 buckets from HTML content
        s3_buckets = extract_s3_buckets(html_content)
        unique_buckets = []
        seen_buckets = set()
        
        for bucket_name in s3_buckets:
            if bucket_name not in seen_buckets:
                seen_buckets.add(bucket_name)
                bucket_url = f"https://{bucket_name}.s3.amazonaws.com"
                
                # Check bucket accessibility
                access_info = check_s3_bucket_access(bucket_url, timeout, headers)
                
                unique_buckets.append({
                    "bucket_name": bucket_name,
                    "bucket_url": bucket_url,
                    "status_code": access_info["status_code"],
                    "status_text": access_info["status_text"],
                    "accessible": access_info["accessible"]
                })
        
        result_entry["s3_buckets"] = unique_buckets
        result_entry["success"] = True
        
    except Exception:
        pass
    
    return result_entry

def analyze_multiple_subdomains(subdomains: List[str], timeout: int = 10, 
                               max_threads: int = 10, protocols: List[str] = None, headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    Analyze multiple subdomains for S3 bucket references.
    
    Args:
        subdomains: List of subdomains to analyze
        timeout: Request timeout in seconds
        max_threads: Maximum number of concurrent threads
        protocols: List of protocols to try (defaults to ['https://', 'http://'])
        headers: Optional custom headers to include in requests
        
    Returns:
        List of dictionaries, each containing subdomain analysis results
        
    Example:
        >>> subdomains = ['example.com', 'test.example.com']
        >>> results = analyze_multiple_subdomains(subdomains)
        >>> for result in results:
        ...     if result['s3_buckets']:
        ...         print(f"Found buckets on {result['subdomain']}")
    """
    if protocols is None:
        protocols = ["https://", "http://"]
    
    results = []
    lock = threading.Lock()
    threads = []
    
    def worker(subdomain):
        result = analyze_subdomain_for_s3_buckets(subdomain, timeout, protocols, headers)
        with lock:
            results.append(result)
    
    for subdomain in subdomains:
        thread = threading.Thread(target=worker, args=(subdomain,))
        threads.append(thread)
        thread.start()
        
        # Limit concurrent threads
        if len(threads) >= max_threads:
            for t in threads:
                t.join()
            threads = []
    
    # Wait for remaining threads
    for t in threads:
        t.join()
    
    return results

# analyze a single subdomain (CLI version)
# main function
def main():
    parser = argparse.ArgumentParser(description="Analyze Javascript files from given subdomain(s) for S3 buckets.")
    parser.add_argument("-u", "--subdomain", help="single subdomain")
    parser.add_argument("-d", "--domain", help="base/root domain (optional, will auto-detect if not provided)")
    parser.add_argument("-l", "--list", help="file containing a list of subdomains")
    parser.add_argument("-t", "--threads", type=int, default=10, help="number of threads (default: 10)")
    parser.add_argument("-timeout", type=int, default=10, help="timeout for HTTP requests (default: 10s)")
    parser.add_argument("-o", "--output", help="output file in JSON format")
    parser.add_argument("-header", action="append", help="custom header to include in requests (can be used multiple times). Format: 'Header: value'")
    parser.add_argument("-silent", action="store_true", help="suppress all output except raw JSON")
    parser.add_argument("-resume", action="store_true", help="resume previous scan from jsbucket.info file")

    args = parser.parse_args()
    info_file = "jsbucket.info"
    
    # Show banner and version info (unless silent)
    if not args.silent:
        # Import version from package
        try:
            from . import __version__
        except ImportError:
            # Fallback for development/standalone execution
            __version__ = "dev"
        
        print_banner()
        log_info(f"Current jsbucket version: v{__version__}")
        log_info(f"Loaded with {args.threads} threads and {args.timeout}s timeout")
    
    try:
        # Handle resume functionality
        if args.resume:
            session_data = load_progress(info_file)
            if not session_data:
                if not args.silent:
                    log_error("No previous scan found to resume.")
                exit(1)
            
            # Restore session info
            input_file = session_data['input_file']
            start_position = session_data['current_position'] + 1  # Resume from next line
            previous_results = session_data.get('results_with_buckets', [])
            
            # Restore args from session
            for key, value in session_data['args'].items():
                setattr(args, key, value)
            
            if not args.silent:
                _console.print(f"� Resuming from line {start_position + 1} of {input_file}", style=progress_style)
                _console.print(f"   Completed: {session_data['completed_count']}/{session_data['total_subdomains']} subdomains", style=progress_style)
                if session_data.get('last_processed_subdomain'):
                    _console.print(f"   Last processed: {session_data['last_processed_subdomain']}", style=progress_style)
        
        else:
            # Normal mode - set up new scan
            if not args.subdomain and not args.list:
                parser.error("Either -u/--subdomain or -l/--list must be provided.")
            
            # Clean up any existing info file
            if os.path.exists(info_file):
                os.remove(info_file)
            
            # Handle single subdomain vs file
            if args.subdomain:
                # Create temporary file for single subdomain
                input_file = '.jsbucket_temp_subdomains.txt'
                with open(input_file, 'w') as f:
                    f.write(args.subdomain + '\n')
                total_lines = 1
            else:
                input_file = args.list
                if not args.silent:
                    log_info("Counting subdomains...")
                total_lines = count_file_lines(input_file)
                if not args.silent:
                    log_info(f"Current scan: {total_lines:,}")
            
            start_position = 0
            previous_results = []
            session_data = create_session_data(input_file, total_lines, args)
            save_progress(info_file, session_data)
        
        # Show domain grouping information (if not resuming or silent)
        if not args.resume and not args.silent and not args.subdomain:
            from collections import defaultdict
            
            # Quick scan to show domain groups
            domain_groups = defaultdict(int)
            try:
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        subdomain = line.strip()
                        if subdomain:
                            base_domain = extract_base_domain(subdomain)
                            domain_groups[base_domain] += 1
                
                if len(domain_groups) > 1:
                    log_info(f"Auto-detected {len(domain_groups)} base domain(s) for scanning")
                    
                    # Show top domains for large lists  
                    if len(domain_groups) > 10:
                        sorted_domains = sorted(domain_groups.items(), key=lambda x: x[1], reverse=True)
                        top_domains = sorted_domains[:10]
                        log_info("Top domains for scanning:")
                        for domain, count in top_domains:
                            _console.print(f"   • {domain}: {count:,} subdomains", style=normal_style)
                        if len(sorted_domains) > 10:
                            remaining = sum(count for _, count in sorted_domains[10:])
                            _console.print(f"   • ... and {len(sorted_domains) - 10} more domains ({remaining:,} subdomains)", style=dim_style)
                    else:
                        log_info("Domain breakdown:")
                        for domain, count in sorted(domain_groups.items()):
                            _console.print(f"   • {domain}: {count} subdomain{'s' if count != 1 else ''}", style=normal_style)
            except Exception:
                pass  # Skip domain analysis if file reading fails

        # Set up worker pool and streaming processing
        lock = threading.Lock()
        all_results = list(previous_results)  # Start with previous results if resuming
        worker = SubdomainWorker(args, session_data, info_file, lock)
        
        # Set up progress bar
        remaining_count = session_data['total_subdomains'] - session_data['completed_count']
        progress_bar = None if args.silent else tqdm(
            total=remaining_count,
            desc="Analyzing subdomains",
            unit="subdomain",
            dynamic_ncols=True,
            initial=0
        )
        
        # Process subdomains with bounded worker pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            # Submit work using streaming generator
            future_to_line = {}
            
            for line_number, subdomain in stream_subdomains_from_file(input_file, start_position):
                future = executor.submit(worker.process_subdomain, (line_number, subdomain))
                future_to_line[future] = (line_number, subdomain)
                
                # Control backpressure - don't queue too many futures
                if len(future_to_line) >= args.threads * 2:
                    # Wait for some to complete
                    done_futures = []
                    for future in concurrent.futures.as_completed(future_to_line.keys()):
                        result = future.result()
                        all_results.append(result)
                        done_futures.append(future)
                        
                        if progress_bar:
                            progress_bar.update(1)
                        
                        # Remove completed futures to control memory
                        if len(done_futures) >= args.threads:
                            break
                    
                    # Clean up completed futures
                    for future in done_futures:
                        del future_to_line[future]
            
            # Process remaining futures
            for future in concurrent.futures.as_completed(future_to_line.keys()):
                result = future.result()
                all_results.append(result)
                if progress_bar:
                    progress_bar.update(1)
        
        if progress_bar:
            progress_bar.close()
        
        # Final progress save and cleanup
        save_progress(info_file, session_data)
        
        # Clean up temp file for single subdomain
        if args.subdomain and os.path.exists('.jsbucket_temp_subdomains.txt'):
            os.remove('.jsbucket_temp_subdomains.txt')
        
        # Filter and output results
        filtered_results = [result for result in all_results if result.get("s3_buckets")]
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(filtered_results, f, indent=4)
            if not args.silent:
                log_info(f"Results written to {args.output}")
        
        if args.silent:
            print(json.dumps(filtered_results, indent=4))
        else:
            scan_time = "completed"  # You could add actual timing if needed
            if len(filtered_results) > 0:
                log_success(f"Scan completed. Found {len(filtered_results)} S3 buckets!")
            else:
                log_info("Scan completed. No S3 buckets found.")
        
        # Clean up info file on successful completion
        if os.path.exists(info_file):
            os.remove(info_file)
    
    except KeyboardInterrupt:
        if progress_bar:
            progress_bar.close()
        if not args.silent:
            log_warn("Process interrupted by user")
            log_info("Progress saved! Use -resume to continue from where you left off")
        exit(1)
    except Exception as e:
        if progress_bar:
            progress_bar.close()
        if not args.silent:
            log_error(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()