"""MongoDB Atlas Connectivity Diagnostic - Standalone Script.

Tests each layer of the MongoDB connection path independently:
  1. DNS resolution
  2. TCP connectivity
  3. TLS handshake
  4. MongoDB server selection
  5. MongoDB authentication
  6. Ping command

Usage:
    python tools/test_mongodb_connection.py
"""

from __future__ import annotations

import os
import sys
import ssl
import socket
from datetime import datetime

# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[ERROR] python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Safe URI parsing
# ---------------------------------------------------------------------------

def mask_uri(uri: str | None) -> str:
    """Return a safe masked version of the URI (no credentials exposed)."""
    if not uri:
        return "NOT SET"
    try:
        # mongodb+srv://user:pass@host/...
        if "@" in uri:
            scheme_end = uri.find("://")
            at_pos = uri.find("@")
            if scheme_end > 0 and at_pos > scheme_end:
                scheme = uri[:scheme_end + 3]
                host_part = uri[at_pos + 1:]
                return f"{scheme}****:****@{host_part}"
        return uri
    except Exception:
        return "PARSE_ERROR"


def extract_hostname(uri: str | None) -> str | None:
    """Extract hostname from MongoDB URI without exposing credentials."""
    if not uri:
        return None
    try:
        # Remove scheme
        if "://" in uri:
            uri = uri.split("://", 1)[1]
        # Remove credentials
        if "@" in uri:
            uri = uri.split("@", 1)[1]
        # Remove path/query
        if "/" in uri:
            uri = uri.split("/", 1)[0]
        # Remove port
        if ":" in uri:
            uri = uri.rsplit(":", 1)[0]
        return uri.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Diagnostic helpers
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(step: str, success: bool, detail: str = "") -> None:
    status = "PASS" if success else "FAIL"
    symbol = "[+]" if success else "[-]"
    msg = f"  {symbol} {step}: {status}"
    if detail:
        msg += f" - {detail}"
    print(msg)


def print_error(step: str, exc: Exception) -> None:
    print(f"  [✗] {step}: FAIL")
    print(f"       Exception type:  {type(exc).__name__}")
    print(f"       Exception msg:   {str(exc)[:200]}")


# ---------------------------------------------------------------------------
# Layer 1: DNS Resolution
# ---------------------------------------------------------------------------

def test_dns_resolution(hostname: str) -> tuple[bool, list[str]]:
    """Test DNS resolution for the hostname."""
    print_header("LAYER 1: DNS Resolution")
    print(f"  Hostname: {hostname}")

    try:
        # For mongodb+srv, we need to check SRV records
        # But first test basic A record resolution
        addrinfo = socket.getaddrinfo(hostname, 27017, socket.AF_INET, socket.SOCK_STREAM)
        ips = list(set(info[4][0] for info in addrinfo))
        print_result("A record resolution", True, f"IPs: {', '.join(ips[:5])}")
        return True, ips
    except socket.gaierror as e:
        print_result("A record resolution", False, f"socket.gaierror: {e}")
        return False, []
    except Exception as e:
        print_error("A record resolution", e)
        return False, []


def test_srv_resolution(hostname: str) -> tuple[bool, list[str]]:
    """Test SRV record resolution for mongodb+srv URIs."""
    print_header("LAYER 1b: SRV Record Resolution")

    try:
        import dns.resolver
    except ImportError:
        print("  [!] dnspython not installed - skipping SRV test")
        return False, []

    # SRV records are at _mongodb._tcp.<hostname>
    # But for Atlas, the hostname IS the SRV target
    # We need to extract the actual domain for SRV lookup
    parts = hostname.split(".", 1)
    if len(parts) < 2:
        print("  [!] Cannot determine SRV domain from hostname")
        return False, []

    domain = parts[1]  # e.g., "1noqlfn.mongodb.net"
    srv_name = f"_mongodb._tcp.{domain}"

    print(f"  SRV query: {srv_name}")

    try:
        answers = dns.resolver.resolve(srv_name, "SRV")
        hosts = []
        for rdata in answers:
            host = str(rdata.target).rstrip(".")
            port = rdata.port
            hosts.append(f"{host}:{port}")
        print_result("SRV resolution", True, f"Hosts: {', '.join(hosts[:3])}")
        return True, hosts
    except dns.resolver.NXDOMAIN:
        print_result("SRV resolution", False, "NXDOMAIN - no SRV records found")
        return False, []
    except dns.resolver.NoAnswer:
        print_result("SRV resolution", False, "NoAnswer - SRV query returned no results")
        return False, []
    except Exception as e:
        print_error("SRV resolution", e)
        return False, []


# ---------------------------------------------------------------------------
# Layer 2: TCP Connectivity
# ---------------------------------------------------------------------------

def test_tcp_connectivity(host: str, port: int = 27017, timeout: int = 10) -> bool:
    """Test basic TCP connectivity to host:port."""
    print_header("LAYER 2: TCP Connectivity")
    print(f"  Target: {host}:{port}")
    print(f"  Timeout: {timeout}s")

    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        print_result("TCP connection", True, f"Connected to {host}:{port}")
        return True
    except socket.timeout:
        print_result("TCP connection", False, "Connection timed out")
        return False
    except ConnectionRefusedError:
        print_result("TCP connection", False, "Connection refused")
        return False
    except OSError as e:
        print_result("TCP connection", False, f"OSError: {e}")
        return False
    except Exception as e:
        print_error("TCP connection", e)
        return False


# ---------------------------------------------------------------------------
# Layer 3: TLS Handshake
# ---------------------------------------------------------------------------

def test_tls_handshake(hostname: str, port: int = 27017, timeout: int = 10) -> tuple[bool, str]:
    """Test TLS handshake with certificate verification."""
    print_header("LAYER 3: TLS Handshake")
    print(f"  Target: {hostname}:{port}")

    try:
        import certifi
        ca_file = certifi.where()
        print(f"  CA bundle: {ca_file}")
        print(f"  CA bundle exists: {os.path.exists(ca_file)}")
    except ImportError:
        print("  [!] certifi not installed")
        ca_file = None

    sock = None
    tls_sock = None
    try:
        # Create TCP connection
        sock = socket.create_connection((hostname, port), timeout=timeout)

        # Create SSL context with certificate verification
        ctx = ssl.create_default_context(cafile=ca_file)
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

        # Perform TLS handshake
        tls_sock = ctx.wrap_socket(sock, server_hostname=hostname)

        # Get TLS details
        protocol = tls_sock.version()
        cipher = tls_sock.cipher()
        cert = tls_sock.getpeercert()

        print_result("TLS handshake", True, f"Protocol: {protocol}, Cipher: {cipher[0]}")
        print(f"  Server cert subject: {cert.get('subject', 'N/A')}")
        print(f"  Server cert issuer: {cert.get('issuer', 'N/A')}")
        print(f"  Server cert not_after: {cert.get('notAfter', 'N/A')}")
        return True, "tls_success"

    except ssl.SSLCertVerificationError as e:
        print_result("TLS handshake", False, "Certificate verification failed")
        print(f"       Error: {e}")
        return False, "tls_cert_verification"

    except ssl.SSLError as e:
        error_msg = str(e).lower()
        if "tlsv1 alert" in error_msg or "internal error" in error_msg:
            print_result("TLS handshake", False, "TLS alert - likely middlebox interference")
            print(f"       Error: {e}")
            return False, "tls_alert_internal_error"
        elif "certificate" in error_msg:
            print_result("TLS handshake", False, "Certificate error")
            print(f"       Error: {e}")
            return False, "tls_certificate_error"
        elif "handshake" in error_msg:
            print_result("TLS handshake", False, "Handshake failure")
            print(f"       Error: {e}")
            return False, "tls_handshake_failure"
        else:
            print_result("TLS handshake", False, f"SSL error: {e}")
            return False, "tls_ssl_error"

    except socket.timeout:
        print_result("TLS handshake", False, "Connection timed out during handshake")
        return False, "tcp_timeout"

    except OSError as e:
        print_result("TLS handshake", False, f"Network error: {e}")
        return False, "network_error"

    except Exception as e:
        print_error("TLS handshake", e)
        return False, "unknown_error"

    finally:
        if tls_sock:
            try:
                tls_sock.close()
            except Exception:
                pass
        elif sock:
            try:
                sock.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Layer 4-6: MongoDB Operations
# ---------------------------------------------------------------------------

def test_mongodb_connection(uri: str) -> None:
    """Test full MongoDB connection with ping."""
    print_header("LAYER 4-6: MongoDB Connection & Ping")

    try:
        import pymongo
        from pymongo import MongoClient
        from pymongo.errors import (
            ServerSelectionTimeoutError,
            ConnectionFailure,
            OperationFailure,
            ConfigurationError,
        )
    except ImportError:
        print("  [!] pymongo not installed")
        return

    import certifi

    client = None
    try:
        print(f"  Creating MongoClient with certifi CA bundle...")
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
            tls=True,
            tlsCAFile=certifi.where(),
        )
        print("  [+] MongoClient created")

        print("  Executing: client.admin.command('ping')")
        start = datetime.now()
        result = client.admin.command("ping")
        elapsed = (datetime.now() - start).total_seconds()
        print_result("MongoDB ping", True, f"Response time: {elapsed:.2f}s")
        print(f"  Response: {result}")

        # Test database access
        db_name = uri.split("/")[-1].split("?")[0] if "/" in uri else "test"
        if not db_name:
            db_name = "test"
        print(f"  Accessing database: {db_name}")
        db = client[db_name]
        collections = db.list_collection_names()
        print_result("Database access", True, f"Collections: {len(collections)}")

    except ConfigurationError as e:
        print_result("MongoDB connection", False, "Configuration error")
        print(f"       Error: {e}")
        print("       Category: CONFIGURATION")

    except ServerSelectionTimeoutError as e:
        error_msg = str(e).lower()
        print_result("MongoDB connection", False, "Server selection timeout")
        print(f"       Error: {e}")
        if "ssl" in error_msg or "tls" in error_msg or "handshake" in error_msg:
            print("       Category: TLS (failure occurs during TLS handshake)")
            print("       Evidence: Error mentions SSL/TLS/handshake")
        elif "connection" in error_msg:
            print("       Category: NETWORK (connection failure)")
        else:
            print("       Category: TIMEOUT (server selection timeout)")

    except ConnectionFailure as e:
        print_result("MongoDB connection", False, "Connection failure")
        print(f"       Error: {e}")
        print("       Category: NETWORK")

    except OperationFailure as e:
        if "authentication" in str(e).lower() or e.code in (13, 18):
            print_result("MongoDB connection", False, "Authentication failed")
            print(f"       Error: {e}")
            print("       Category: AUTHENTICATION")
            print("       Note: TLS succeeded but credentials rejected")
        else:
            print_result("MongoDB connection", False, "Operation failure")
            print(f"       Error: {e}")
            print("       Category: MONGODB_OPERATION")

    except Exception as e:
        print_error("MongoDB connection", e)
        print("       Category: UNKNOWN")

    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main diagnostic
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  MongoDB Atlas Connectivity Diagnostic")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Print environment info
    print_header("ENVIRONMENT")
    print(f"  Python:    {sys.version.split()[0]}")
    print(f"  OpenSSL:   {ssl.OPENSSL_VERSION.split()[1]}")
    try:
        import pymongo
        print(f"  PyMongo:   {pymongo.__version__}")
    except ImportError:
        print("  PyMongo:   NOT INSTALLED")
    try:
        import certifi
        print(f"  certifi:   {certifi.__version__}")
        print(f"  CA path:   {certifi.where()}")
    except ImportError:
        print("  certifi:   NOT INSTALLED")
    try:
        import dns.resolver
        print(f"  dnspython: INSTALLED")
    except ImportError:
        print("  dnspython: NOT INSTALLED")

    # Load URI
    uri = os.getenv("MONGODB_URI")
    print_header("CONFIGURATION")
    print(f"  MONGODB_URI: {mask_uri(uri)}")
    print(f"  URI present:  {'YES' if uri else 'NO'}")

    if not uri:
        print("\n[ABORT] MONGODB_URI not found in environment")
        return

    # Extract hostname
    hostname = extract_hostname(uri)
    print(f"  Hostname:    {hostname}")

    is_srv = uri.startswith("mongodb+srv://")
    print(f"  SRV URI:     {'YES' if is_srv else 'NO'}")

    # Layer 1: DNS
    dns_ok, ips = test_dns_resolution(hostname)

    srv_hosts = []
    if is_srv and dns_ok:
        srv_ok, srv_hosts = test_srv_resolution(hostname)
    elif is_srv:
        # Even if A record fails, try SRV (PyMongo uses dnspython for SRV)
        srv_ok, srv_hosts = test_srv_resolution(hostname)

    # Layer 2: TCP (test first resolved IP or SRV host)
    tcp_ok = False
    tcp_target = None
    if ips:
        tcp_target = ips[0]
        tcp_ok = test_tcp_connectivity(tcp_target, 27017)
    elif srv_hosts:
        # Test TCP to first SRV host
        srv_host = srv_hosts[0].split(":")[0]
        srv_port = int(srv_hosts[0].split(":")[1]) if ":" in srv_hosts[0] else 27017
        tcp_target = f"{srv_host}:{srv_port}"
        tcp_ok = test_tcp_connectivity(srv_host, srv_port)
    elif hostname:
        tcp_ok = test_tcp_connectivity(hostname, 27017)

    # Layer 3: TLS
    tls_ok, tls_category = False, "not_tested"
    if ips:
        tls_ok, tls_category = test_tls_handshake(ips[0], 27017)
    elif srv_hosts:
        srv_host = srv_hosts[0].split(":")[0]
        srv_port = int(srv_hosts[0].split(":")[1]) if ":" in srv_hosts[0] else 27017
        tls_ok, tls_category = test_tls_handshake(srv_host, srv_port)
    elif hostname:
        tls_ok, tls_category = test_tls_handshake(hostname, 27017)

    # Layer 4-6: Full MongoDB connection
    test_mongodb_connection(uri)

    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    print(f"  DNS Resolution:     {'PASS' if dns_ok else 'FAIL'}")
    if is_srv:
        print(f"  SRV Resolution:     {'PASS' if srv_hosts else 'FAIL'}")
    print(f"  TCP Connectivity:   {'PASS' if tcp_ok else 'FAIL'}")
    print(f"  TLS Handshake:      {'PASS' if tls_ok else 'FAIL'}")
    if not tls_ok:
        print(f"  TLS Failure Type:   {tls_category}")

    # Determine exact failing layer
    print()
    if not dns_ok and not srv_hosts:
        print("  EXACT FAILING LAYER: DNS Resolution")
        print("  EVIDENCE: Cannot resolve hostname to IP address")
        print("  ACTION: Check DNS settings, try nslookup from command line")
    elif not tcp_ok:
        print("  EXACT FAILING LAYER: TCP Connectivity")
        print("  EVIDENCE: Cannot establish TCP connection to port 27017")
        print("  ACTION: Check firewall rules, network connectivity to Atlas")
    elif not tls_ok:
        print("  EXACT FAILING LAYER: TLS Handshake")
        print(f"  EVIDENCE: {tls_category}")
        if tls_category == "tls_alert_internal_error":
            print("  ANALYSIS: TLSV1_ALERT_INTERNAL_ERROR indicates a middlebox")
            print("            (antivirus, firewall, or proxy) is interfering")
            print("            with the TLS handshake.")
            print("  ACTION: Disable antivirus SSL scanning, try different network")
        else:
            print("  ACTION: Check TLS configuration, certificates")
    else:
        print("  All layers passed - check MongoDB authentication")

    print()
    print("=" * 60)
    print("  Diagnostic complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
