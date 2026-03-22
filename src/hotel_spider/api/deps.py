from collections.abc import Generator

from sqlalchemy.orm import Session

from hotel_spider.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
