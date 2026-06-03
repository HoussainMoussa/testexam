"""Network server module for domain directory using Protocol C.

Protocol C (JSON lines) justification:
- Human-readable format for debugging and logging
- Self-delimiting with newlines (no length prefix overhead)
- Native JSON support in Python (json module)
- Easy to extend with new fields
- Compatible with Unix pipes and text tools
- Simpler than binary protocols while maintaining structure

Commands:
  SEARCH <hote>    - Return domain details or error
  RECORD <hote>    - Collect and record new domain
  COUNT            - Return number of domains
  LIST             - Return all hostnames
"""

import json
import logging
import socketserver
from typing import Any

from donnees import chercher, enregistrer, lister
from collecte import collecter

logger = logging.getLogger(__name__)


class AnnuaireRequestHandler(socketserver.StreamRequestHandler):
    """Request handler for domain directory commands.

    Uses Protocol C (JSON lines) for communication.
    """

    def handle(self) -> None:
        """Handle incoming client connection."""
        try:
            while True:
                # Read until newline
                line = self.rfile.readline().decode("utf-8").strip()
                if not line:
                    break

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    self._send_response({"error": "INVALID_JSON"})
                    continue

                cmd = data.get("cmd")
                arg = data.get("arg")

                if cmd == "SEARCH":
                    self._handle_search(arg)
                elif cmd == "RECORD":
                    self._handle_record(arg)
                elif cmd == "COUNT":
                    self._handle_count()
                elif cmd == "LIST":
                    self._handle_list()
                else:
                    logger.warning(f"Unknown command: {cmd}")
                    self._send_response({"error": "UNKNOWN_COMMAND"})

        except Exception as e:
            logger.error(f"Handler error: {e}")
            try:
                self._send_response({"error": "INTERNAL_ERROR"})
            except Exception:
                pass

    def _handle_search(self, hote: str) -> None:
        """Handle SEARCH command."""
        if not hote:
            self._send_response({"error": "MISSING_ARGUMENT"})
            return

        domaine = chercher(hote)
        if domaine:
            self._send_response(
                {
                    "hote": domaine.hote,
                    "ip": domaine.ip,
                    "contact": domaine.contact,
                    "email": domaine.email,
                }
            )
        else:
            self._send_response({"error": "NOT_FOUND"})

    def _handle_record(self, hote: str) -> None:
        """Handle RECORD command."""
        if not hote:
            self._send_response({"error": "MISSING_ARGUMENT"})
            return

        try:
            domaine = collecter(hote)
            enregistrer(domaine)
            self._send_response({"status": "OK"})
        except ValueError:
            self._send_response({"status": "ALREADY_EXISTS"})
        except Exception as e:
            logger.error(f"Record error: {e}")
            self._send_response({"status": "ERROR", "msg": str(e)})

    def _handle_count(self) -> None:
        """Handle COUNT command."""
        try:
            domaines = lister()
            self._send_response({"count": len(domaines)})
        except Exception as e:
            logger.error(f"Count error: {e}")
            self._send_response({"error": str(e)})

    def _handle_list(self) -> None:
        """Handle LIST command."""
        try:
            domaines = lister()
            hotes = [d.hote for d in domaines]
            self._send_response({"hotes": hotes})
        except Exception as e:
            logger.error(f"List error: {e}")
            self._send_response({"error": str(e)})

    def _send_response(self, response: dict[str, Any]) -> None:
        """Send JSON response to client."""
        try:
            line = json.dumps(response) + "\\n"
            self.wfile.write(line.encode("utf-8"))
        except Exception as e:
            logger.error(f"Send response error: {e}")


class AnnuaireServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Multi-threaded TCP server for domain directory."""

    allow_reuse_address = True


def start_server(host: str, port: int) -> None:
    """Start the domain directory server.

    Args:
        host: Server host address
        port: Server port number
    """
    server = AnnuaireServer((host, port), AnnuaireRequestHandler)
    logger.info(f"Server started at {host}:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    finally:
        server.server_close()
        logger.info("Server closed")
