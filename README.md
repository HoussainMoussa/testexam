# Annuaire - Networked Domain Directory

A Python CLI application for managing a networked directory of hostnames, their IP addresses, and WHOIS contact information.

## Features

- **Data Collection**: Resolve hostnames to IP addresses using `nslookup` and retrieve WHOIS contact information
- **Persistent Storage**: SQLite database with SQLAlchemy ORM
- **Network Server**: Multi-threaded TCP server using Protocol C (JSON lines)
- **Command-Line Interface**: Easy-to-use CLI with multiple verbosity levels
- **Protocol C Justification**: JSON lines format is human-readable, self-delimiting, and easy to extend

## Installation

### Prerequisites

- Python 3.12+
- `whois` command-line tool (Linux/macOS) or Windows equivalent

### System Setup

On Debian/Ubuntu:
```bash
apt install whois
```

On macOS:
```bash
brew install whois
```

On Windows:
Download from https://www.nirsoft.net/utils/whois.html or use WSL.

### Python Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd testexam
```

2. Create virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure `.env`:
```bash
cp .env.example .env
# Edit .env to customize HOST and PORT if needed
```

## Usage

### Start Server

```bash
python cli.py serve
# Or with custom host/port:
python cli.py serve --host 0.0.0.0 --port 9999
```

### Search Domain

```bash
python cli.py search mines-ales.fr
# Output:
# Hostname: mines-ales.fr
# IP: 185.22.173.39
# Contact: Contact Name
# Email: contact@example.com
```

### Record Domain

```bash
python cli.py record mines-ales.fr
# Collects IP and WHOIS info, stores in database
# Output: Status: OK
```

### Count Domains

```bash
python cli.py count
# Output: Total domains: 5
```

### List Domains

```bash
python cli.py list
# Output:
# mines-ales.fr
# example.com
# google.com
```

### Verbosity Levels

```bash
# No output (only results)
python cli.py search example.com

# Info level logging
python cli.py -v search example.com

# Debug level logging
python cli.py -vv search example.com

# Detailed logging with timestamps, file, line, thread
python cli.py -vvv search example.com
```

## Architecture

### Modules

- **collecte.py**: Data collection (IP resolution, WHOIS queries)
- **donnees.py**: Database persistence layer (SQLAlchemy ORM, CRUD operations)
- **serveur.py**: Multi-threaded TCP server with Protocol C
- **client.py**: Client library for server communication
- **cli.py**: Command-line interface with argparse

### Protocol C (JSON Lines)

Justification for Protocol C (JSON lines over TCP):

1. **Human-readable**: Easy to debug, log, and inspect
2. **Self-delimiting**: Newlines separate messages, no length prefix needed
3. **Native Python support**: `json` module available in standard library
4. **Extensible**: Easy to add new fields to commands
5. **Unix-friendly**: Works with pipes, grep, and standard tools
6. **Simpler than binary**: No endianness, encoding issues
7. **Stateless**: Each command is independent

**Example Protocol Exchange**:

```
Client -> Server:
{"cmd": "SEARCH", "arg": "example.com"}\n

Server -> Client:
{"hote": "example.com", "ip": "93.184.216.34", "contact": "John Doe", "email": "john@example.com"}\n

Client -> Server:
{"cmd": "RECORD", "arg": "test.com"}\n

Server -> Client:
{"status": "OK"}\n

Client -> Server:
{"cmd": "COUNT"}\n

Server -> Client:
{"count": 42}\n

Client -> Server:
{"cmd": "LIST"}\n

Server -> Client:
{"hotes": ["example.com", "test.com", "mines-ales.fr"]}\n
```

## Database

Domain records are stored in `domaines.db` (SQLite) with the following schema:

| Column  | Type    | Nullable | Notes |
|---------|---------|----------|-------|
| hote    | String  | No       | Primary key |
| ip      | String  | Yes      | IPv4 address |
| contact | String  | Yes      | Registrant name |
| email   | String  | Yes      | Registrant email |

## Testing

Run pytest tests for data layer:

```bash
pytest test_donnees.py -v
```

Tests cover:
- Recording new domains
- Duplicate domain detection
- Domain search
- Domain listing
- Optional field handling
- Pydantic validation

## Error Handling

- All exceptions are caught specifically (no bare `except`)
- Errors logged to stderr
- Server graceful shutdown on Ctrl+C
- Connection errors handled on client side
- Socket timeouts set to 15 seconds

## Environment Variables

Configured in `.env` file:

- `HOST` (default: 127.0.0.1)
- `PORT` (default: 8888)

## Example Workflow

```bash
# Terminal 1: Start server
python cli.py -v serve

# Terminal 2: Record a domain
python cli.py -v record google.com

# Terminal 3: Search the domain
python cli.py search google.com

# Check count
python cli.py count

# List all
python cli.py list
```

## Dependencies

- **pydantic**: Data validation and parsing
- **email-validator**: Email validation for Pydantic
- **sqlalchemy**: ORM for database operations
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework

## License

MIT
