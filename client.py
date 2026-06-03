"""Client module for domain directory using raw sockets.

Implements Protocol C (JSON lines) client-side communication.
"""

import json
import logging
import socket
from typing import Optional

from collecte import Domaine

logger = logging.getLogger(__name__)

# Server configuration (will be set by CLI)
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8888


def set_server_config(host: str, port: int) -> None:
    """Set server host and port.

    Args:
        host: Server hostname or IP
        port: Server port number
    """
    global SERVER_HOST, SERVER_PORT
    SERVER_HOST = host
    SERVER_PORT = port


def _send_command(cmd: str, arg: Optional[str] = None) -> Optional[dict]:
    """Send command to server and receive response.

    Args:
        cmd: Command name (SEARCH, RECORD, COUNT, LIST)
        arg: Optional argument

    Returns:
        Response dictionary or None on error
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)

        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            logger.debug(f"Connected to {SERVER_HOST}:{SERVER_PORT}")

            # Build and send command
            request = {"cmd": cmd}
            if arg:
                request["arg"] = arg

            message = json.dumps(request) + "\\n"
            s.sendall(message.encode("utf-8"))
            logger.debug(f"Sent: {message.strip()}")

            # Read response until newline
            response_data = b""
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                response_data += chunk
                if b"\\n" in response_data:
                    break

            response_str = response_data.decode("utf-8").strip()
            logger.debug(f"Received: {response_str}")
            return json.loads(response_str)

        except ConnectionRefusedError:
            logger.error(f"Connection refused to {SERVER_HOST}:{SERVER_PORT}")
            return None
        except socket.timeout:
            logger.error("Socket timeout")
            return None
        finally:
            s.close()

    except Exception as e:
        logger.error(f"Command error: {e}")
        return None


def cmd_search(hote: str) -> Optional[Domaine]:
    """Search for domain by hostname.

    Args:
        hote: Hostname to search

    Returns:
        Domaine object or None if not found or error
    """
    response = _send_command("SEARCH", hote)
    if not response:
        return None

    if "error" in response:
        logger.warning(f"Search error: {response['error']}")
        return None

    try:
        return Domaine(
            hote=response.get("hote"),
            ip=response.get("ip"),
            contact=response.get("contact"),
            email=response.get("email"),
        )
    except Exception as e:
        logger.error(f"Failed to parse response: {e}")
        return None


def cmd_record(hote: str) -> str:
    """Record a new domain.

    Args:
        hote: Hostname to record

    Returns:
        Status string ("OK", "ALREADY_EXISTS", or "ERROR")
    """
    response = _send_command("RECORD", hote)
    if not response:
        return "ERROR"

    if "status" in response:
        return response["status"]
    elif "error" in response:
        return "ERROR"
    else:
        return "ERROR"


def cmd_count() -> int:
    """Get count of recorded domains.

    Returns:
        Number of domains or 0 on error
    """
    response = _send_command("COUNT")
    if not response:
        return 0

    if "count" in response:
        return response["count"]
    else:
        return 0


def cmd_list() -> list[str]:
    """Get list of all recorded hostnames.

    Returns:
        List of hostnames or empty list on error
    """
    response = _send_command("LIST")
    if not response:
        return []

    if "hotes" in response:
        return response["hotes"]
    else:
        return []
