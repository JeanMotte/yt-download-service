from fastapi import APIRouter

router = APIRouter()


@router.get("/login")
async def login():
    """Endpoint for user login."""
    # This will be implemented later
    return {"message": "Login endpoint"}
