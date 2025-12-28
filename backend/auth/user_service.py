"""
User management service
"""
from models import User
from models.database import SessionLocal
from typing import Optional


def get_or_create_user(clerk_user_id: str, email: Optional[str] = None, name: Optional[str] = None) -> User:
    """Get existing user or create new one in database"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
        
        if not user:
            user = User(
                clerk_user_id=clerk_user_id,
                email=email,
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created new user: {email}")
        else:
            if email and user.email != email:
                user.email = email
                db.commit()
        
        return user
    finally:
        db.close()
