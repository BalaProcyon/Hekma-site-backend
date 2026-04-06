from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from fastapi import HTTPException

class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def get_user(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def create_user(self, user_create: UserCreate):
        existing_user = self.user_repo.get_by_email(user_create.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        return self.user_repo.create(user_create)
