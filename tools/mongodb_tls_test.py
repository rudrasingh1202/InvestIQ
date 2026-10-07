"""
MongoDB Atlas TLS Connection Diagnostic Tool

Tests the MongoDB connection environment without modifying any application data.
"""

import sys
import os
import ssl
import socket
import platform
from urllib.parse import urlparse

# Load .env
from dotenv import load_dotenv
load_dotenv()

def mask_uri(uri):
    """Mask password in URI for safe display."""
    if not uri or '@' not in uri:
        return uri or "NOT SET"
    try:
        parsed = urlparse(uri)
        if parsed.password:
            return uri.replace(f":{parsed.password}@", ":****@", 1)
        return uri
    except:
        return "INVALID URI"

def test_dns(hostname):
    """Test DNS resolution."""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror:
        # Try SRV
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", 'SRV')
            targets = [str(rdata.target).rstrip('.') for rdata in answers]
            return True, f"SRV -> {', '.join(targets)}"
        except:
            return False, "DNS resolution failed"
    except Exception as e:
        return False, str(e)

def test_tcp(host, port):
    """Test TCP connectivity."""
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        return True
    except Exception as e:
        return False

def test_tls(host, port):
    """Test TLS handshake."""
    try:
        sock = socket.create_connection((host, port), timeout=10)
        ctx = ssl.create_default_context()
        tls_sock = ctx.wrap_socket(sock, server_hostname=host)
        version = tls_sock.version()
        tls_sock.close()
        return True, version
    except Exception as e:
        return False, str(e)[:100]

def test_mongodb_ping(uri):
    """Test MongoDB ping."""
    try:
        from pymongo import MongoClient
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        result = client.admin.command("ping")
        client.close()
        return True, str(result)
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:150]}"

def main():
    print("=" * 60)
    print("MONGODB ATLAS TLS DIAGNOSTIC")
    print("=" * 60)

    # Phase 1: Environment
    print("\n[1. ENVIRONMENT]")
    print(f"  Python: {sys.version}")
    print(f"  Python Path: {sys.executable}")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  OpenSSL: {ssl.OPENSSL_VERSION}")

    try:
        import pymongo
        print(f"  PyMongo: {pymongo.__version__}")
    except ImportError:
        print("  PyMongo: NOT INSTALLED")

    try:
        import certifi
        print(f"  certifi: {certifi.__version__}")
        print(f"  certifi CA bundle: {certifi.where()}")
    except ImportError:
        print("  certifi: NOT INSTALLED")

    try:
        import dns.resolver
        print(f"  dnspython: INSTALLED")
    except ImportError:
        print("  dnspython: NOT INSTALLED")

    # Phase 2: Configuration
    print("\n[2. CONFIGURATION]")
    uri = os.getenv("MONGODB_URI", "").strip()
    db_name = os.getenv("MONGODB_DATABASE", "investiq").strip()

    if not uri:
        print("  MONGODB_URI: NOT SET")
        return

    print(f"  MONGODB_URI: {mask_uri(uri)}")
    print(f"  MONGODB_DATABASE: {db_name}")

    parsed = urlparse(uri)
    hostname = parsed.hostname
    port = parsed.port or 27017

    # Phase 3: DNS
    print(f"\n[3. DNS RESOLUTION] ({hostname})")
    dns_ok, dns_result = test_dns(hostname)
    print(f"  Result: {'PASS' if dns_ok else 'FAIL'} - {dns_result}")

    # Get shard hostnames for further tests
    shard_host = hostname
    if dns_ok and "SRV" in str(dns_result):
        import dns.resolver
        answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", 'SRV')
        shard_host = str(answers[0].target).rstrip('.')
        print(f"  Shard host: {shard_host}")

    # Phase 4: TCP
    print(f"\n[4. TCP CONNECTIVITY] ({shard_host}:{port})")
    tcp_ok = test_tcp(shard_host, port)
    print(f"  Result: {'PASS' if tcp_ok else 'FAIL'}")

    # Phase 5: TLS
    print(f"\n[5. TLS HANDSHAKE] ({shard_host}:{port})")
    tls_ok, tls_result = test_tls(shard_host, port)
    print(f"  Result: {'PASS' if tls_ok else 'FAIL'} - {tls_result}")

    # Phase 6: MongoDB Ping
    print(f"\n[6. MONGODB PING]")
    ping_ok, ping_result = test_mongodb_ping(uri)
    print(f"  Result: {'PASS' if ping_ok else 'FAIL'} - {ping_result}")

    # Phase 7: CA Bundle Verification
    print(f"\n[7. CA BUNDLE VERIFICATION]")
    try:
        import certifi
        ctx = ssl.create_default_context()
        print(f"  Default SSL context created: OK")
        print(f"  CA bundle path: {certifi.where()}")
        print(f"  CA bundle exists: {os.path.exists(certifi.where())}")
    except Exception as e:
        print(f"  CA bundle check failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if ping_ok:
        print("  STATUS: SUCCESS - MongoDB connection is working!")
    elif not dns_ok:
        print("  FAILURE LAYER: DNS Resolution")
        print("  ACTION: Check internet connection and DNS settings")
    elif not tcp_ok:
        print("  FAILURE LAYER: TCP Connectivity")
        print("  ACTION: Check firewall/port 27017")
    elif not tls_ok:
        print("  FAILURE LAYER: TLS Handshake")
        print("  LIKELY CAUSE: Antivirus/Windows Defender SSL inspection")
        print("  ACTION: Disable antivirus SSL scanning or try different network")
    else:
        print("  FAILURE LAYER: Unknown")
        print("  ACTION: Check MongoDB Atlas status and credentials")

    return ping_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
