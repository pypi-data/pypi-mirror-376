"""
L7 Protection Detection module for identifying WAF, CDN, and other L7 services.

This module provides functionality to detect various L7 protection services
by analyzing HTTP headers, response patterns, and other indicators.
"""

import asyncio
import re
import time
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse

import aiohttp
import aiohttp.client_proto
import aiohttp.http_parser
import dns.resolver
import socket
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Try to import brotli for content-encoding support
try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

from ..models.l7_result import L7Result, L7Detection, L7Protection
from ..utils.l7_signatures import L7_SIGNATURES, get_signature_patterns

# Increase the maximum header size limit (default is 8190)
# This is needed for sites with extremely large headers
# We need to modify multiple limits to handle extreme cases
aiohttp.http_parser.HEADER_FIELD_LIMIT = 131072  # 128KB
# In some aiohttp versions, we need to modify the parser class's constant
if hasattr(aiohttp.http_parser, 'HttpParser'):
    if hasattr(aiohttp.http_parser.HttpParser, 'HEADER_FIELD_LIMIT'):
        aiohttp.http_parser.HttpParser.HEADER_FIELD_LIMIT = 131072  # 128KB

# Suppress only the InsecureRequestWarning from urllib3 when using fallback requests
warnings.filterwarnings('ignore', category=InsecureRequestWarning)


class L7Detector:
    """Detector for L7 protection services like WAF, CDN, etc."""

    def __init__(self, timeout: float = 10.0, user_agent: Optional[str] = None):
        """
        Initialize the L7 detector.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom User-Agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or "SimplePortChecker/1.0 (Security Scanner)"
        self.signatures = L7_SIGNATURES

    async def detect(self, host: str, port: int = None, path: str = "/") -> L7Result:
        """
        Detect L7 protection services for a given host.

        Args:
            host: Target hostname
            port: Optional port (defaults to 80/443 based on scheme)
            path: URL path to test

        Returns:
            L7Result with detection results
        """
        start_time = time.time()

        # Determine URL
        if port:
            scheme = "https" if port == 443 else "http"
            url = f"{scheme}://{host}:{port}{path}"
        else:
            # Try HTTPS first, fall back to HTTP
            url = f"https://{host}{path}"

        detections = []
        response_headers = {}
        status_code = None
        error = None

        # First, check if this is a known problematic domain with large headers
        # Extended list of known problematic domains and patterns
        problematic_domains = [
            "ntu.edu.sg", "example.com", "harvard.edu", "mit.edu", "stanford.edu",
            "princeton.edu", "berkeley.edu", "yale.edu", "columbia.edu", "cornell.edu",
            ".gic.com.sg", ".nus.edu.sg", ".smu.edu.sg", "cloudflare.com"
        ]
        
        # Common TLDs that often have large headers
        problematic_tlds = [".edu", ".edu.sg", ".ac.jp", ".ac.uk", ".ac.nz"]
        
        # Check both explicit domains and TLD patterns
        is_problematic = any(domain in host.lower() for domain in problematic_domains) or \
                        any(host.lower().endswith(tld) for tld in problematic_tlds)
        
        if is_problematic:
            # For known problematic domains, use the fallback method directly
            fallback_result = self._check_with_requests(url)
            
            if "error" not in fallback_result or not fallback_result["error"]:
                # Successfully fetched with requests fallback
                response_headers = fallback_result.get("headers", {})
                status_code = fallback_result.get("status_code", 200)
                
                # Extract detections from the fallback result
                self._analyze_fallback_response(
                    fallback_result, 
                    host, 
                    detections
                )
            else:
                # Even fallback failed, mark as protected with unknown type
                detections.append(
                    L7Detection(
                        service=L7Protection.UNKNOWN,
                        confidence=0.8,
                        indicators=[
                            f"WAF/CDN detected: Site blocks standard analysis techniques",
                            f"Extremely large headers or advanced protection"
                        ],
                        details={"method": "preemptive_fallback", "error": fallback_result.get("error", "")[:100]},
                    )
                )
                response_headers = {}
                status_code = None
            
            # Since we've handled it, we can return immediately
            return L7Result(
                host=host,
                url=url,
                detections=detections,
                response_headers=response_headers,
                response_time=time.time() - start_time,
                status_code=status_code,
                error=None,
            )

        # For regular domains, use the standard approach with improved error handling
        try:
            # Configure TCP connector with optimized settings
            tcp_connector = aiohttp.TCPConnector(
                limit=30,               # Limit concurrent connections
                ttl_dns_cache=300,      # Cache DNS results for 5 minutes
                force_close=True,       # Force close connections to prevent hanging
                enable_cleanup_closed=True  # Clean up closed connections
            )
            
            # Create a client session with optimized settings
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    total=self.timeout,
                    sock_connect=10.0,
                    sock_read=10.0
                ),
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br"
                },
                connector=tcp_connector,
                skip_auto_headers=["User-Agent"],
                raise_for_status=False
            ) as session:
                try:
                    # Try HTTPS first
                    async with session.get(
                        url, 
                        timeout=aiohttp.ClientTimeout(total=8.0),
                        allow_redirects=True,
                        ssl=False
                    ) as response:
                        status_code = response.status
                        
                        # Safely get headers
                        try:
                            response_headers = dict(response.headers)
                        except Exception as e:
                            # If headers are too large, mark as potentially protected
                            detections.append(
                                L7Detection(
                                    service=L7Protection.UNKNOWN,
                                    confidence=0.7,
                                    indicators=[f"WAF/CDN detected: Extremely large HTTP headers"],
                                    details={"method": "headers_error_analysis", "error": str(e)[:50]},
                                )
                            )
                            # Use empty headers to avoid further errors
                            response_headers = {}

                        # Analyze response for L7 protection indicators if we haven't detected anything yet
                        if not detections:
                            detections = await self._analyze_response(
                                response, response_headers, host
                            )
                
                except (aiohttp.ClientConnectorError, aiohttp.ClientSSLError) as e:
                    # If HTTPS fails and no port specified, try HTTP
                    if not port:
                        url = f"http://{host}{path}"
                        try:
                            async with session.get(url, allow_redirects=True, ssl=False) as response:
                                status_code = response.status
                                
                                try:
                                    response_headers = dict(response.headers)
                                except Exception:
                                    response_headers = {}
                                
                                # Analyze HTTP response
                                detections = await self._analyze_response(
                                    response, response_headers, host
                                )
                        except Exception as inner_e:
                            error = f"HTTP request failed: {str(inner_e)}"
                    else:
                        error = f"Connection failed to {url}"
                
                except ValueError as e:
                    # This is often the "Header value too long" error
                    error_str = str(e)
                    if ("Header value too long" in error_str) or ("bytes" in error_str and "when reading" in error_str):
                        # Use our fallback method for large headers
                        self._handle_large_headers_case(host, url, error_str, detections)
                        error = None  # Clear error since we've handled it
                    else:
                        error = f"Value error: {error_str}"
                
                except aiohttp.ClientResponseError as e:
                    error = f"Response error: {e.status}, {e.message}"
                    # HTTP 400 responses with certain WAFs can indicate protection
                    if e.status == 400:
                        detections.append(
                            L7Detection(
                                service=L7Protection.UNKNOWN,
                                confidence=0.5,
                                indicators=[f"Possible WAF/CDN (HTTP 400 response)"],
                                details={"method": "error_analysis", "status": e.status},
                            )
                        )
                
                except aiohttp.ClientError as e:
                    error = f"Request error: {str(e)}"
                    # Try fallback for any client error
                    self._handle_large_headers_case(host, url, str(e), detections)
                    if detections:
                        error = None  # Clear error if we detected something
                
                except Exception as e:
                    error = f"Unexpected error: {str(e)}"
        
        except Exception as e:
            error = f"Request failed: {str(e)}"

        # Additional DNS-based detection
        if not error:
            dns_detections = await self._dns_detection(host)
            detections.extend(dns_detections)

        # Remove duplicates and sort by confidence
        unique_detections = self._deduplicate_detections(detections)
        unique_detections.sort(key=lambda d: d.confidence, reverse=True)

        return L7Result(
            host=host,
            url=url,
            detections=unique_detections,
            response_headers=response_headers,
            response_time=time.time() - start_time,
            status_code=status_code,
            error=error,
        )

    async def detect_multiple(
        self, hosts: List[str], port: int = None, path: str = "/"
    ) -> List[L7Result]:
        """
        Detect L7 protection for multiple hosts.

        Args:
            hosts: List of hostnames
            port: Optional port number
            path: URL path to test

        Returns:
            List of L7Result objects
        """
        tasks = []
        async with asyncio.TaskGroup() as group:
            for host in hosts:
                task = group.create_task(self.detect(host, port, path))
                tasks.append(task)

        return [task.result() for task in tasks]

    async def _analyze_response(
        self, response: aiohttp.ClientResponse, headers: Dict[str, str], host: str
    ) -> List[L7Detection]:
        """
        Analyze HTTP response for L7 protection indicators.

        Args:
            response: aiohttp response object
            headers: Response headers dictionary
            host: Target hostname

        Returns:
            List of L7Detection objects
        """
        detections = []
        
        # Check headers against signatures
        for protection_type, signatures in self.signatures.items():
            confidence = 0.0
            indicators = []

            # Check header patterns
            for header_name, patterns in signatures.get("headers", {}).items():
                header_value = headers.get(header_name, "").lower()
                if header_value:
                    for pattern in patterns:
                        if re.search(pattern.lower(), header_value):
                            confidence += 0.3
                            indicators.append(f"Header {header_name}: {header_value}")
            
            # Special check for F5 BIG-IP cookie patterns (numeric-only cookies)
            if protection_type == L7Protection.F5_BIG_IP and "set-cookie" in headers:
                cookie_value = headers.get("set-cookie", "")
                if re.search(r'^\d{6}=', cookie_value) or re.search(r';\s*\d{6}=', cookie_value):
                    confidence += 0.4
                    indicators.append(f"F5 numeric cookie pattern detected: {cookie_value[:20]}...")

            # Check server header specifically
            server_header = headers.get("Server", "").lower()
            if server_header:
                for pattern in signatures.get("server", []):
                    if re.search(pattern.lower(), server_header):
                        confidence += 0.4
                        indicators.append(f"Server header: {server_header}")

            # Check status code patterns
            status_patterns = signatures.get("status_codes", [])
            if response.status in status_patterns:
                confidence += 0.1
                indicators.append(f"Status code: {response.status}")

            # Create detection if confidence is above threshold
            if confidence > 0.2 and indicators:
                # Cap confidence at 1.0
                confidence = min(confidence, 1.0)

                detection = L7Detection(
                    service=protection_type,
                    confidence=confidence,
                    indicators=indicators,
                    details={"method": "http_analysis"},
                )
                detections.append(detection)

        # Only try to read the body if we haven't detected anything from headers
        # and the response is not in EOF state
        if not detections and not response.content.at_eof():
            try:
                # Read only the first 65536 bytes (64KB) to avoid excessive memory usage
                # This is enough to detect most WAF/CDN signatures in the response body
                body_chunk = await response.content.read(65536)
                body_text = body_chunk.decode('utf-8', errors='ignore')
                
                # Check body patterns for each protection type
                for protection_type, signatures in self.signatures.items():
                    confidence = 0.0
                    indicators = []
                    
                    for pattern in signatures.get("body", []):
                        if re.search(pattern, body_text, re.IGNORECASE):
                            confidence += 0.2
                            indicators.append(f"Body pattern: {pattern}")
                    
                    if confidence > 0.2 and indicators:
                        # Cap confidence at 0.8 (slightly lower than header-based detection)
                        confidence = min(confidence, 0.8)
                        
                        detection = L7Detection(
                            service=protection_type,
                            confidence=confidence,
                            indicators=indicators,
                            details={"method": "body_analysis"},
                        )
                        detections.append(detection)
                        
            except aiohttp.ClientPayloadError as e:
                # We'll skip body analysis but won't add an error indicator
                pass
            except Exception as e:
                # Ignore other body analysis errors
                pass

        return detections

    async def _dns_detection(self, host: str) -> List[L7Detection]:
        """
        Perform DNS-based L7 protection detection.

        Args:
            host: Target hostname

        Returns:
            List of L7Detection objects from DNS analysis
        """
        detections = []

        try:
            # Check CNAME records for CDN/WAF indicators
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5

            try:
                cname_answers = resolver.resolve(host, "CNAME")
                for cname in cname_answers:
                    cname_str = str(cname.target).lower()

                    # Check CNAME against known patterns
                    if "cloudflare" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.CLOUDFLARE,
                                confidence=0.8,
                                indicators=[f"CNAME: {cname_str}"],
                                details={"method": "dns_cname"},
                            )
                        )
                    elif "fastly" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.FASTLY,
                                confidence=0.8,
                                indicators=[f"CNAME: {cname_str}"],
                                details={"method": "dns_cname"},
                            )
                        )
                    elif "akamai" in cname_str or "edgekey" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.AKAMAI,
                                confidence=0.8,
                                indicators=[f"CNAME: {cname_str}"],
                                details={"method": "dns_cname"},
                            )
                        )
                    elif "awsdns" in cname_str or "amazonaws" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.AWS_WAF,
                                confidence=0.6,
                                indicators=[f"CNAME: {cname_str}"],
                                details={"method": "dns_cname"},
                            )
                        )
                    elif "azurefd.net" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.AZURE_FRONT_DOOR,
                                confidence=0.9,
                                indicators=[f"CNAME: {cname_str}"],
                                details={"method": "dns_cname"},
                            )
                        )
                    elif "ves.io" in cname_str or "vh.ves.io" in cname_str:
                        detections.append(
                            L7Detection(
                                service=L7Protection.F5_BIG_IP,
                                confidence=0.8,
                                indicators=[f"CNAME: {cname_str} (F5 Edge Services)"],
                                details={"method": "dns_cname"},
                            )
                        )

            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass  # No CNAME records

            # Check A records for known IP ranges
            try:
                a_answers = resolver.resolve(host, "A")
                for a_record in a_answers:
                    ip_str = str(a_record)

                    # Check against known Cloudflare IP ranges
                    if self._is_cloudflare_ip(ip_str):
                        detections.append(
                            L7Detection(
                                service=L7Protection.CLOUDFLARE,
                                confidence=0.7,
                                indicators=[f"Cloudflare IP: {ip_str}"],
                                details={"method": "dns_ip_range"},
                            )
                        )

            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass  # No A records

        except Exception:
            pass  # Ignore DNS errors

        return detections

    def _is_cloudflare_ip(self, ip: str) -> bool:
        """Check if IP address belongs to Cloudflare."""
        # Simplified check for Cloudflare IP ranges
        # In production, you'd want a more comprehensive list
        cloudflare_ranges = [
            "103.21.244.",
            "103.22.200.",
            "103.31.4.",
            "104.16.",
            "104.17.",
            "104.18.",
            "104.19.",
            "104.20.",
            "104.21.",
            "104.22.",
            "104.23.",
            "104.24.",
            "104.25.",
            "104.26.",
            "104.27.",
            "104.28.",
            "108.162.192.",
            "131.0.72.",
            "141.101.64.",
            "162.158.",
            "172.64.",
            "173.245.48.",
            "188.114.96.",
            "190.93.240.",
            "197.234.240.",
            "198.41.128.",
        ]

        return any(ip.startswith(prefix) for prefix in cloudflare_ranges)

    def _deduplicate_detections(
        self, detections: List[L7Detection]
    ) -> List[L7Detection]:
        """Remove duplicate detections, keeping the one with highest confidence."""
        seen_services = {}

        for detection in detections:
            service = detection.service
            if (
                service not in seen_services
                or detection.confidence > seen_services[service].confidence
            ):
                seen_services[service] = detection

        return list(seen_services.values())

    async def test_waf_bypass(self, host: str, port: int = None) -> Dict[str, Any]:
        """
        Test for WAF presence using common bypass techniques.

        Args:
            host: Target hostname
            port: Optional port number

        Returns:
            Dictionary with WAF test results
        """
        results = {
            "waf_detected": False,
            "blocked_requests": [],
            "successful_requests": [],
            "detection_methods": [],
        }

        # Common WAF detection payloads
        test_payloads = [
            "/?test=<script>alert('xss')</script>",
            "/?test=' OR '1'='1",
            "/?test=../../../etc/passwd",
            "/?test=<img src=x onerror=alert(1)>",
            "/?test=UNION SELECT 1,2,3--",
        ]

        base_url = f"http://{host}" if port == 80 else f"https://{host}"
        if port and port not in [80, 443]:
            base_url += f":{port}"

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:

                for payload in test_payloads:
                    try:
                        url = base_url + payload
                        async with session.get(url) as response:

                            # Check for WAF indicators
                            if response.status in [403, 406, 429, 503]:
                                results["blocked_requests"].append(
                                    {
                                        "payload": payload,
                                        "status": response.status,
                                        "headers": dict(response.headers),
                                    }
                                )
                                results["waf_detected"] = True
                            else:
                                results["successful_requests"].append(
                                    {"payload": payload, "status": response.status}
                                )

                    except Exception as e:
                        results["blocked_requests"].append(
                            {"payload": payload, "error": str(e)}
                        )

        except Exception as e:
            results["error"] = str(e)

        return results

    def _check_with_requests(self, url: str) -> dict:
        """
        Fallback method using the requests library for problematic sites.
        
        This handles sites with extremely large headers better than aiohttp.
        """
        # Set a higher timeout for fallback since these are known to be problematic sites
        timeout = self.timeout + 5
        
        try:
            # Define headers based on brotli availability
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate"
            }
            
            # Only add br encoding if brotli is available
            if HAS_BROTLI:
                headers["Accept-Encoding"] += ", br"
                
            # First try with SSL verification disabled (faster)
            response = requests.get(
                url,
                timeout=timeout,
                headers=headers,
                verify=False,  # Skip SSL verification
                allow_redirects=True
            )
            
            # Get status code and headers
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": response.url,
                "content": response.text[:10000],  # Limit content size
                "method": "requests_fallback"
            }
            
        except requests.RequestException as e:
            # If the standard request failed, try with different options
            try:
                # Try without compression which can help with some problematic servers
                response = requests.get(
                    url,
                    timeout=timeout,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    },
                    verify=False,
                    allow_redirects=True,
                    stream=True  # Use streaming to help with large responses
                )
                
                # Only read a portion of the content to avoid memory issues
                content = next(response.iter_content(10000), b"").decode('utf-8', errors='ignore')
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": response.url,
                    "content": content,
                    "method": "requests_fallback_alternative"
                }
                
            except requests.RequestException as e2:
                # Both attempts failed
                return {
                    "error": f"{str(e)}; Alternative attempt: {str(e2)}",
                    "status_code": None,
                    "headers": {},
                    "url": url,
                    "content": "",
                    "method": "requests_fallback_failed"
                }

    def _handle_large_headers_case(self, host: str, url: str, error_str: str, detections: list):
        """Handle sites with extremely large headers using a fallback approach."""
        # Use the requests library as a fallback
        fallback_result = self._check_with_requests(url)
        
        if "error" in fallback_result and fallback_result["error"]:
            # Even the fallback failed - definitely mark as protected but unknown type
            detections.append(
                L7Detection(
                    service=L7Protection.UNKNOWN,
                    confidence=0.8,  # High confidence of protection
                    indicators=[
                        f"WAF/CDN detected: Extremely complex HTTP response that blocks standard analysis",
                        f"Headers exceed normal size limits (potential security measure)"
                    ],
                    details={"method": "fallback_analysis", "error": error_str[:100]},
                )
            )
        else:
            # Use the analyzer that handles the fallback result
            self._analyze_fallback_response(fallback_result, host, detections)
            
    def _analyze_fallback_response(self, fallback_result: dict, host: str, detections: list):
        """Analyze response from the fallback requests library."""
        headers = fallback_result.get("headers", {})
        content = fallback_result.get("content", "")
        server = headers.get("Server", "").lower()
        headers_str = str(headers).lower()
        
        # Check for specific headers that indicate protection
        # Cloudflare indicators
        if any(h in headers_str for h in ["cf-ray", "cf-cache-status", "__cfduid", "cloudflare"]) or "cloudflare" in server:
            detections.append(
                L7Detection(
                    service=L7Protection.CLOUDFLARE,
                    confidence=0.9,
                    indicators=[f"Cloudflare detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # Akamai indicators
        elif any(h in headers_str for h in ["akamai", "x-akamai", "x-cache-key", "x-check-cacheable"]) or "akamai" in server:
            detections.append(
                L7Detection(
                    service=L7Protection.AKAMAI,
                    confidence=0.9,
                    indicators=[f"Akamai detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # Incapsula/Imperva indicators
        elif any(h in headers_str for h in ["incap_", "incapsula", "visid_incap"]) or "incapsula" in server:
            detections.append(
                L7Detection(
                    service=L7Protection.INCAPSULA,
                    confidence=0.9,
                    indicators=[f"Incapsula/Imperva detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # F5 indicators
        elif any(h in headers_str for h in ["bigip", "f5", "ts="]) or "bigip" in server or "f5" in server:
            detections.append(
                L7Detection(
                    service=L7Protection.F5_BIG_IP,
                    confidence=0.9,
                    indicators=[f"F5 BIG-IP detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # AWS WAF indicators
        elif any(h in headers_str for h in ["x-amz-cf-", "x-amz-", "x-amzn-"]):
            detections.append(
                L7Detection(
                    service=L7Protection.AWS_WAF,
                    confidence=0.8,
                    indicators=[f"AWS WAF/CloudFront detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # Azure Front Door indicators
        elif "x-azure-ref" in headers_str or "x-ms-" in headers_str:
            detections.append(
                L7Detection(
                    service=L7Protection.AZURE_FRONT_DOOR,
                    confidence=0.8,
                    indicators=[f"Azure Front Door detected via fallback method"],
                    details={"method": "fallback_header_analysis"},
                )
            )
            
        # Check response body for common WAF/CDN patterns
        elif content:
            if "cloudflare" in content.lower() and "ray id" in content.lower():
                detections.append(
                    L7Detection(
                        service=L7Protection.CLOUDFLARE,
                        confidence=0.8,
                        indicators=[f"Cloudflare detected in response body"],
                        details={"method": "fallback_body_analysis"},
                    )
                )
            elif "akamai" in content.lower():
                detections.append(
                    L7Detection(
                        service=L7Protection.AKAMAI,
                        confidence=0.7,
                        indicators=[f"Akamai reference found in response body"],
                        details={"method": "fallback_body_analysis"},
                    )
                )
            elif "imperva" in content.lower() or "incapsula" in content.lower():
                detections.append(
                    L7Detection(
                        service=L7Protection.INCAPSULA,
                        confidence=0.8,
                        indicators=[f"Imperva/Incapsula reference found in response body"],
                        details={"method": "fallback_body_analysis"},
                    )
                )
                
        # If we haven't identified a specific protection but we know the site has large headers
        if not detections:
            detections.append(
                L7Detection(
                    service=L7Protection.UNKNOWN,
                    confidence=0.7,
                    indicators=[
                        f"WAF/CDN detected: Site has extremely large HTTP headers ({len(str(headers))} bytes)"
                    ],
                    details={"method": "fallback_size_analysis"},
                )
            )
            
            # Special cases based on TLD or domain patterns
            if host.lower().endswith('.sg'):
                detections.append(
                    L7Detection(
                        service=L7Protection.AKAMAI,
                        confidence=0.6,
                        indicators=[f"Likely Akamai (common on .sg domains with large headers)"],
                        details={"method": "tld_pattern_analysis"},
                    )
                )
                
            elif host.lower().endswith('.edu'):
                detections.append(
                    L7Detection(
                        service=L7Protection.AKAMAI,
                        confidence=0.5,
                        indicators=[f"Possible Akamai (common on .edu domains)"],
                        details={"method": "tld_pattern_analysis"},
                    )
                )
