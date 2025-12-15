"""
Initialize the database
"""
from .database import engine, Base
from . import Scan, ZombieResource, RightSizingRecommendation

def init_db():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()
