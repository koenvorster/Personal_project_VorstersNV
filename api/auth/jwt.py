"""
VorstersNV Authenticatie via Keycloak JWKS
Tokens worden gevalideerd met Keycloak's publieke sleutels.
Rollen worden gelezen uit de Keycloak realm_access claim.
"""
import os
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from pydantic import BaseModel

from db.models.user import UserRole

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "vorstersNV")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "vorstersNV-api")

JWKS_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

bearer_scheme = HTTPBearer(auto_error=False)

# In-memory JWKS cache (herlaad bij fout)
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


# ── Schemas ──────────────────────────────────────────────────────────────────

class TokenData(BaseModel):
    user_id: str
    email: str
    naam: str
    rol: UserRole


class UserResponse(BaseModel):
    id: int
    naam: str
    email: str
    rol: UserRole
    actief: bool
    aangemaakt_op: str

    model_config = {"from_attributes": True}


# ── Token validatie ───────────────────────────────────────────────────────────

async def _valideer_keycloak_token(token: str) -> TokenData:
    global _jwks_cache
    try:
        jwks = await _get_jwks()
        header = jwt.get_unverified_header(token)
        # Zoek de juiste sleutel op basis van kid
        key = next(
            (k for k in jwks["keys"] if k.get("kid") == header.get("kid")),
            None,
        )
        if key is None:
            # Cache verlopen — forceer herlaad
            _jwks_cache = None
            jwks = await _get_jwks()
            key = next((k for k in jwks["keys"] if k.get("kid") == header.get("kid")), None)
        if key is None:
            raise HTTPException(status_code=401, detail="Onbekende token-sleutel")

        public_key = jwk.construct(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=KEYCLOAK_CLIENT_ID,
            issuer=ISSUER,
            options={"verify_aud": False},  # audience optioneel in dev
        )

        # Rollen uit Keycloak realm_access claim halen
        realm_roles: list[str] = payload.get("realm_access", {}).get("roles", [])
        rol = UserRole.klant
        if "admin" in realm_roles:
            rol = UserRole.admin
        elif "tester" in realm_roles:
            rol = UserRole.tester

        return TokenData(
            user_id=payload.get("sub", ""),
            email=payload.get("email", payload.get("preferred_username", "")),
            naam=payload.get("name", payload.get("preferred_username", "")),
            rol=rol,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ongeldig of verlopen token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependencies ─────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenData:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geen token opgegeven",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _valideer_keycloak_token(credentials.credentials)


async def require_admin(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    if current_user.rol != UserRole.admin:
        raise HTTPException(status_code=403, detail="Alleen admins hebben toegang")
    return current_user


async def require_admin_or_tester(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    if current_user.rol not in (UserRole.admin, UserRole.tester):
        raise HTTPException(status_code=403, detail="Alleen admins en testers hebben toegang")
    return current_user
