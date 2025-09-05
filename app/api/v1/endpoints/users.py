from fastapi import APIRouter, Depends
from app.api import deps
from app.schemas.user import UserCreate

router = APIRouter()


# Função auxiliar para formatar a resposta
def user_helper(user) -> dict:
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
    if current_user:
        return user_helper(current_user)
    return {"msg": "User not found"}
