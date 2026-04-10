"""
VorstersNV Auth Router — Keycloak SSO
Login/registratie verloopt via Keycloak (http://localhost:8080).
Dit router biedt /me en gebruikersbeheer endpoints.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth.jwt import (
    TokenData, UserResponse,
    get_current_user, require_admin,
)
from db.models.user import UserRole

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Ingelogde gebruiker ophalen",
)
async def get_me(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """Haal de gegevens van de ingelogde Keycloak-gebruiker op."""
    return {
        "id": 0,
        "naam": current_user.naam,
        "email": current_user.email,
        "rol": current_user.rol,
        "actief": True,
        "aangemaakt_op": "–",
    }


@router.get(
    "/gebruikers",
    response_model=list[UserResponse],
    summary="Alle gebruikers (admin)",
    dependencies=[Depends(require_admin)],
)
async def list_gebruikers():
    """Haal alle gebruikers op via Keycloak Admin API. **Alleen voor admins.**"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Gebruikersbeheer loopt via Keycloak Admin: http://localhost:8080",
    )


@router.patch(
    "/gebruikers/{user_id}/rol",
    response_model=UserResponse,
    summary="Rol wijzigen (admin)",
    dependencies=[Depends(require_admin)],
)
async def wijzig_rol(user_id: str, nieuwe_rol: UserRole):
    """Wijzig de rol van een gebruiker via Keycloak. **Alleen voor admins.**"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Rolbeheer loopt via Keycloak Admin: http://localhost:8080",
    )

