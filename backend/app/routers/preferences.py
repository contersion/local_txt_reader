from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas.preferences import UserPreferencesPatchRequest, UserPreferencesResponse
from app.services.preferences import get_user_preferences, update_user_preferences


router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse)
def get_preferences(current_user: CurrentUser) -> UserPreferencesResponse:
    preferences, has_saved_preferences = get_user_preferences(current_user)
    return UserPreferencesResponse.model_validate(
        {
            "has_saved_preferences": has_saved_preferences,
            "preferences": preferences,
        }
    )


@router.patch("", response_model=UserPreferencesResponse)
def patch_preferences(
    payload: UserPreferencesPatchRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    preferences, has_saved_preferences = update_user_preferences(db, current_user, payload)
    return UserPreferencesResponse.model_validate(
        {
            "has_saved_preferences": has_saved_preferences,
            "preferences": preferences,
        }
    )
