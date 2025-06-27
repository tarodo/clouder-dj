import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.spotify import SpotifyAPIClient
from app.core.security import create_access_token, create_refresh_token
from app.repositories.spotify_token import SpotifyTokenRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate

log = structlog.get_logger()


class AuthService:
    def __init__(self, db: AsyncSession, spotify_client: SpotifyAPIClient):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = SpotifyTokenRepository(db)
        self.spotify_client = spotify_client

    async def handle_spotify_callback(
        self, *, code: str, code_verifier: str
    ) -> dict[str, str]:
        log.info("Handling spotify callback", code_len=len(code))
        token_info = await self.spotify_client.exchange_code_for_token(
            code, code_verifier
        )
        user_profile = await self.spotify_client.get_user_profile(
            token_info["access_token"]
        )

        spotify_id = user_profile["id"]

        try:
            user = await self.user_repo.get_by_spotify_id(spotify_id=spotify_id)
            if user:
                log.info("User found, updating profile", spotify_id=spotify_id)
                user_in_update = UserUpdate(
                    display_name=user_profile.get("display_name"),
                    email=user_profile.get("email"),
                )
                user = await self.user_repo.update(db_obj=user, obj_in=user_in_update)
            else:
                log.info("User not found, creating new user", spotify_id=spotify_id)
                user_in_create = UserCreate(
                    spotify_id=spotify_id,
                    display_name=user_profile.get("display_name"),
                    email=user_profile.get("email"),
                )
                user = await self.user_repo.create(obj_in=user_in_create)
                await self.db.flush()  # Flush to get the user ID

            await self.token_repo.create_or_update(user=user, token_info=token_info)
            log.info("Spotify token created/updated for user", spotify_id=spotify_id)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            log.exception(
                "Failed to handle spotify callback during DB operations",
                spotify_id=spotify_id,
            )
            raise

        access_token = create_access_token(data={"sub": spotify_id})
        refresh_token = create_refresh_token(data={"sub": spotify_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
