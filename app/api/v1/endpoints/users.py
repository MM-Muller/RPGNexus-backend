from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.api import deps
from app.schemas.user import UserUpdate
from app.crud import user as crud_user
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


# Função auxiliar para formatar a resposta
def user_helper(user) -> dict:
    if not user:
        return {}
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
    }


@router.get("/me")
async def read_users_me(current_user=Depends(deps.get_current_user)):
    """
    Retorna as informações do usuário logado.
    """
    return user_helper(current_user)


@router.put("/me")
async def update_user_me(
    user_update: UserUpdate,
    current_user=Depends(deps.get_current_user),
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
):
    """
    Atualiza as informações do usuário logado.
    """
    user_id = str(current_user["_id"])
    updated_user = await crud_user.update_user(
        db, user_id=user_id, user_update=user_update
    )
    return user_helper(updated_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    current_user=Depends(deps.get_current_user),
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
):
    """
    Deleta a conta do usuário logado.
    """
    user_id = str(current_user["_id"])
    deleted = await crud_user.delete_user(db, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
