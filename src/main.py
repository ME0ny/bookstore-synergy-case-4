from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.utils import get_openapi
from src.api.routers.auth_router import router as auth_router
from src.api.routers.test_router import router as test_router
from src.api.routers.admin_router import router as admin_router
from src.api.routers.books_router import router as books_router
from src.api.routers.purchase_router import router as purchase_router

app = FastAPI()

# Подключаем роутер для авторизации
app.include_router(auth_router)
app.include_router(test_router)
app.include_router(admin_router)
app.include_router(books_router)
app.include_router(purchase_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bookstore API!"}