"""Data persistence module using SQLAlchemy ORM.

Manages domain records in SQLite database with CRUD operations
using Pydantic models for API boundaries.
"""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import Session, declarative_base

from collecte import Domaine

logger = logging.getLogger(__name__)

# Database configuration
BDD_PATH = Path(__file__).parent / "domaines.db"
Base = declarative_base()


class DomaineORM(Base):
    """SQLAlchemy ORM model for domain records."""

    __tablename__ = "domaines"

    hote = Column(String, primary_key=True, nullable=False)
    ip = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    email = Column(String, nullable=True)

    def to_pydantic(self) -> Domaine:
        """Convert ORM model to Pydantic model."""
        return Domaine(
            hote=self.hote, ip=self.ip, contact=self.contact, email=self.email
        )


# Create engine and tables
engine = create_engine(f"sqlite:///{BDD_PATH}")
Base.metadata.create_all(engine)
logger.debug(f"Database initialized at {BDD_PATH}")


def enregistrer(domaine: Domaine) -> None:
    """Insert a new domain record.

    Args:
        domaine: Domaine object to insert

    Raises:
        ValueError: If domain already exists
    """
    with Session(engine) as session:
        existing = session.query(DomaineORM).filter_by(hote=domaine.hote).first()
        if existing:
            logger.warning(f"Domain {domaine.hote} already exists")
            raise ValueError(f"Domain {domaine.hote} already exists")

        orm_obj = DomaineORM(
            hote=domaine.hote, ip=domaine.ip, contact=domaine.contact, email=domaine.email
        )
        session.add(orm_obj)
        session.commit()
        logger.info(f"Recorded domain {domaine.hote}")


def lister() -> list[Domaine]:
    """List all domain records.

    Returns:
        List of Domaine objects
    """
    with Session(engine) as session:
        records = session.query(DomaineORM).all()
        return [record.to_pydantic() for record in records]


def chercher(hote: str) -> Optional[Domaine]:
    """Search for a domain by hostname.

    Args:
        hote: Hostname to search for

    Returns:
        Domaine object or None if not found
    """
    with Session(engine) as session:
        record = session.query(DomaineORM).filter_by(hote=hote).first()
        if record:
            logger.debug(f"Found domain {hote}")
            return record.to_pydantic()
        logger.debug(f"Domain {hote} not found")
        return None
