from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.db.database import get_db

router = APIRouter()

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate, 
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    """
    return user_service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int, 
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID.
    """
    return user_service.get_user(user_id)
