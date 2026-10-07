"""
MongoDB Atlas connection diagnostic script for InvestIQ.

This script tests the MongoDB connection and reports any issues.
It does NOT modify any data in the database.

Usage:
    python scripts/test_mongodb.py
"""

import sys
import os
import ssl
import socket
import platform
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv


def mask_uri(uri: str) -> str:
    """Mask the password in a MongoDB URI for safe display."""
    if not uri or '@' not in uri:
        return uri or "NOT SET"
    try:
        parsed = urlparse(uri)
        if parsed.password:
            # Replace password with ****
            masked = uri.replace(f":{parsed.password}@", ":****@", 1)
            return masked
        return uri
    except Exception:
        return "INVALID URI FORMAT"


def test_dns_resolution(hostname: str) -> bool:
    """Test DNS resolution for a hostname."""
    try:
        # Try A record first
        ip = socket.gethostbyname(hostname)
        print(f"  DNS resolution: SUCCESS ({ip})")
        return True
    except socket.gaierror:
        # For SRV-based connections, the hostname may not have an A record
        # Try SRV record lookup
        try:
            import dns.resolver
            srv_hostname = f"_mongodb._tcp.{hostname}"
            answers = dns.resolver.resolve(srv_hostname, 'SRV')
            targets = [str(rdata.target).rstrip('.') for rdata in answers]
            print(f"  DNS resolution: SUCCESS (SRV -> {', '.join(targets)})")
            return True
        except Exception:
            print(f"  DNS resolution: FAILED (no A or SRV record found)")
            return False
    except Exception as e:
        print(f"  DNS resolution: FAILED ({e})")
        return False


def test_tcp_connection(hostname: str, port: int) -> bool:
    """Test TCP connection to a host:port."""
    # For SRV-based connections, try to resolve to a shard hostname
    target_host = hostname
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror:
        # Try SRV record to get actual shard hostname
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", 'SRV')
            if answers:
                target_host = str(answers[0].target).rstrip('.')
        except Exception:
            pass
    
    try:
        sock = socket.create_connection((target_host, port), timeout=10)
        print(f"  TCP connection to {target_host}:{port}: SUCCESS")
        sock.close()
        return True
    except Exception as e:
        print(f"  TCP connection to {target_host}:{port}: FAILED ({e})")
        return False


def test_tls_handshake(hostname: str, port: int) -> bool:
    """Test TLS handshake with a host:port."""
    # For SRV-based connections, try to resolve to a shard hostname
    target_host = hostname
    try:
        socket.gethostbyname(hostname)
    except socket.gaierror:
        # Try SRV record to get actual shard hostname
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", 'SRV')
            if answers:
                target_host = str(answers[0].target).rstrip('.')
        except Exception:
            pass
    
    try:
        sock = socket.create_connection((target_host, port), timeout=10)
        ctx = ssl.create_default_context()
        tls_sock = ctx.wrap_socket(sock, server_hostname=target_host)
        print(f"  TLS handshake with {target_host}:{port}: SUCCESS ({tls_sock.version()})")
        tls_sock.close()
        return True
    except Exception as e:
        print(f"  TLS handshake with {target_host}:{port}: FAILED ({str(e)[:100]})")
        return False


def test_mongodb_connection(uri: str) -> bool:
    """Test MongoDB connection using PyMongo."""
    try:
        from pymongo import MongoClient
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=15000,
        )
        result = client.admin.command("ping")
        print(f"  MongoDB ping: SUCCESS ({result})")
        client.close()
        return True
    except Exception as e:
        print(f"  MongoDB ping: FAILED ({type(e).__name__})")
        print(f"  Error: {str(e)[:200]}")
        return False


def main():
    print("=" * 60)
    print("InvestIQ MongoDB Connection Diagnostic")
    print("=" * 60)

    # Load environment
    load_dotenv()

    # Environment info
    print("\n[Environment]")
    print(f"  Python: {sys.version}")
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
    except ImportError:
        print("  certifi: NOT INSTALLED")

    try:
        import dns.resolver
        print(f"  dnspython: INSTALLED")
    except ImportError:
        print("  dnspython: NOT INSTALLED")

    # Configuration check
    print("\n[Configuration]")
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DATABASE", "investiq")

    if not mongodb_uri:
        print("  MONGODB_URI: NOT SET")
        print("\nERROR: MONGODB_URI is not configured in .env file")
        return False
    else:
        print(f"  MONGODB_URI: {mask_uri(mongodb_uri)}")
        print(f"  MONGODB_DATABASE: {mongodb_db}")

    # Extract hostname from URI
    try:
        parsed = urlparse(mongodb_uri)
        hostname = parsed.hostname
        port = parsed.port or 27017
    except Exception as e:
        print(f"\nERROR: Invalid MongoDB URI format: {e}")
        return False

    # DNS test
    print(f"\n[DNS Resolution] ({hostname})")
    dns_ok = test_dns_resolution(hostname)

    # TCP test
    print(f"\n[TCP Connection] ({hostname}:{port})")
    tcp_ok = test_tcp_connection(hostname, port)

    # TLS test
    print(f"\n[TLS Handshake] ({hostname}:{port})")
    tls_ok = test_tls_handshake(hostname, port)

    # MongoDB test
    print(f"\n[MongoDB Connection]")
    mongodb_ok = test_mongodb_connection(mongodb_uri)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if mongodb_ok:
        print("  Status: SUCCESS - MongoDB connection is working!")
        return True
    elif not dns_ok:
        print("  Status: FAILED - DNS resolution failed")
        print("  Action: Check your internet connection and DNS settings")
    elif not tcp_ok:
        print("  Status: FAILED - TCP connection failed")
        print("  Action: Check if port 27017 is blocked by firewall")
    elif not tls_ok:
        print("  Status: FAILED - TLS handshake failed")
        print("  Action: This is often caused by:")
        print("    1. Antivirus software with SSL scanning")
        print("    2. Windows Defender network protection")
        print("    3. Corporate firewall or proxy")
        print("\n  Try:")
        print("    - Temporarily disable antivirus SSL scanning")
        print("    - Add Python to antivirus exclusions")
        print("    - Try a different network (mobile hotspot)")
        print("    - Contact your network administrator")
    else:
        print("  Status: FAILED - Unknown error")

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
