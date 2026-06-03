"""Unit tests for donnees.py data persistence layer.

Tests CRUD operations for domain records.
"""

import pytest
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from collecte import Domaine
from donnees import DomaineORM, Base, enregistrer, lister, chercher


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def mock_donnees(monkeypatch, temp_db):
    """Mock the database engine to use temporary database."""
    import donnees
    monkeypatch.setattr(donnees, "engine", temp_db)
    return donnees


def test_enregistrer_nouveau_domaine(mock_donnees):
    """Test recording a new domain."""
    domaine = Domaine(
        hote="example.com",
        ip="93.184.216.34",
        contact="John Doe",
        email="john@example.com",
    )
    mock_donnees.enregistrer(domaine)

    # Verify it was recorded
    result = mock_donnees.chercher("example.com")
    assert result is not None
    assert result.hote == "example.com"
    assert result.ip == "93.184.216.34"
    assert result.contact == "John Doe"


def test_enregistrer_domaine_existant(mock_donnees):
    """Test that recording duplicate domain raises error."""
    domaine = Domaine(
        hote="test.com",
        ip="192.0.2.1",
        contact="Test User",
        email="test@test.com",
    )
    mock_donnees.enregistrer(domaine)

    # Try to record same domain again
    with pytest.raises(ValueError, match="already exists"):
        mock_donnees.enregistrer(domaine)


def test_chercher_domaine_existant(mock_donnees):
    """Test searching for an existing domain."""
    domaine = Domaine(
        hote="found.com",
        ip="10.0.0.1",
        contact="Found User",
        email="found@found.com",
    )
    mock_donnees.enregistrer(domaine)

    result = mock_donnees.chercher("found.com")
    assert result is not None
    assert result.hote == "found.com"
    assert result.ip == "10.0.0.1"


def test_chercher_domaine_inexistant(mock_donnees):
    """Test searching for non-existent domain."""
    result = mock_donnees.chercher("nonexistent.com")
    assert result is None


def test_lister_domaines_vides(mock_donnees):
    """Test listing domains when database is empty."""
    result = mock_donnees.lister()
    assert result == []


def test_lister_domaines_multiples(mock_donnees):
    """Test listing multiple domains."""
    domaines = [
        Domaine(
            hote="test1.com", ip="1.1.1.1", contact="User 1", email="user1@test.com"
        ),
        Domaine(
            hote="test2.com", ip="2.2.2.2", contact="User 2", email="user2@test.com"
        ),
        Domaine(
            hote="test3.com",
            ip=None,
            contact=None,
            email=None,
        ),
    ]

    for d in domaines:
        mock_donnees.enregistrer(d)

    result = mock_donnees.lister()
    assert len(result) == 3
    assert all(isinstance(d, Domaine) for d in result)
    assert {d.hote for d in result} == {"test1.com", "test2.com", "test3.com"}


def test_domaine_pydantic_validation():
    """Test Pydantic model validation."""
    # Valid email
    d = Domaine(
        hote="test.com", ip="1.1.1.1", contact="Test", email="test@test.com"
    )
    assert d.email == "test@test.com"

    # Invalid email should raise
    with pytest.raises(Exception):
        Domaine(hote="test.com", ip="1.1.1.1", contact="Test", email="invalid-email")

    # Missing hote should raise
    with pytest.raises(Exception):
        Domaine(ip="1.1.1.1", contact="Test", email="test@test.com")


def test_optional_fields(mock_donnees):
    """Test recording domain with optional fields as None."""
    domaine = Domaine(hote="minimal.com", ip=None, contact=None, email=None)
    mock_donnees.enregistrer(domaine)

    result = mock_donnees.chercher("minimal.com")
    assert result is not None
    assert result.hote == "minimal.com"
    assert result.ip is None
    assert result.contact is None
    assert result.email is None
