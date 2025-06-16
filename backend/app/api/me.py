from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema, tags=["me"])
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user
