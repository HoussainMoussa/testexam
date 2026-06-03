"""Data collection module for domain information.

Provides functions to resolve hostnames to IP addresses and retrieve
WHOIS contact information using system commands (nslookup and whois).
"""

import logging
import platform
import re
import subprocess
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)


class Domaine(BaseModel):
    """Pydantic model representing a domain record."""

    hote: str = Field(..., description="Hostname (primary key)")
    ip: Optional[str] = Field(None, description="IPv4 address")
    contact: Optional[str] = Field(None, description="Registrant name")
    email: Optional[EmailStr] = Field(None, description="Registrant email")


def resoudre_ip(hote: str) -> Optional[str]:
    """Resolve hostname to IPv4 address using nslookup.

    Args:
        hote: Hostname to resolve

    Returns:
        IPv4 address string or None on failure
    """
    try:
        # Determine OS and build command
        system = platform.system()
        if system == "Windows":
            cmd = ["nslookup", hote]
        else:
            cmd = ["nslookup", hote]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5.0, check=False
        )

        if result.returncode != 0:
            logger.warning(f"nslookup failed for {hote}: return code {result.returncode}")
            return None

        # Parse output to find IPv4 after "Non-authoritative answer" or "Address:"
        lines = result.stdout.split("\n")
        found_answer = False
        for line in lines:
            if "Non-authoritative answer" in line or "Address:" in line:
                found_answer = True
            if found_answer and "Address:" in line:
                # Extract IP address
                parts = line.split(":")
                if len(parts) >= 2:
                    ip = parts[1].strip()
                    # Validate IPv4 format
                    if _is_valid_ipv4(ip):
                        logger.debug(f"Resolved {hote} to {ip}")
                        return ip

        logger.warning(f"No IPv4 address found for {hote}")
        return None

    except FileNotFoundError:
        logger.error(f"nslookup command not found")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"nslookup timeout for {hote}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error resolving {hote}: {e}")
        return None


def interroger_whois(hote: str) -> tuple[Optional[str], Optional[str]]:
    """Query WHOIS information for hostname.

    Args:
        hote: Hostname to query

    Returns:
        Tuple of (contact_name, email) or (None, None) on failure
    """
    try:
        result = subprocess.run(
            ["whois", hote], capture_output=True, text=True, timeout=10.0, check=False
        )

        if result.returncode != 0:
            logger.warning(f"whois failed for {hote}: return code {result.returncode}")
            return (None, None)

        output = result.stdout

        # Extract contact name
        contact = None
        for line in output.split("\n"):
            if "Registrant Name:" in line or "Registrant:" in line:
                contact = line.split(":", 1)[1].strip()
                break

        # Extract first email
        email_match = re.search(r"\S+@\S+", output)
        email = email_match.group(0) if email_match else None

        logger.debug(f"WHOIS for {hote}: contact={contact}, email={email}")
        return (contact, email)

    except FileNotFoundError:
        logger.error(f"whois command not found")
        return (None, None)
    except subprocess.TimeoutExpired:
        logger.error(f"whois timeout for {hote}")
        return (None, None)
    except Exception as e:
        logger.error(f"Unexpected error querying WHOIS for {hote}: {e}")
        return (None, None)


def collecter(hote: str) -> Domaine:
    """Collect domain information by resolving IP and querying WHOIS.

    Args:
        hote: Hostname to collect information for

    Returns:
        Domaine object with collected information
    """
    logger.info(f"Collecting data for {hote}")

    ip = resoudre_ip(hote)
    contact, email = interroger_whois(hote)

    return Domaine(hote=hote, ip=ip, contact=contact, email=email)


def _is_valid_ipv4(ip: str) -> bool:
    """Validate IPv4 address format.

    Args:
        ip: IP address string

    Returns:
        True if valid IPv4 format
    """
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False
