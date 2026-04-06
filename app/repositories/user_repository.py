from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user_create: UserCreate) -> User:
        db_user = User(email=user_create.email, username=user_create.username)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
