import uvicorn

from contextlib import asynccontextmanager
from db.database import engine
from db.models import Base
from fastapi import FastAPI, Response
from routers.admin import router as admin_router
from routers.authentication import router as auth_router 
from routers.items import router as item_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connect:
        await connect.run_sync(Base.metadata.create_all)
    yield
    #async with engine.begin() as connect:
    #    await connect.run_sync(Base.metadata.drop_all)
    
    

app = FastAPI(lifespan=lifespan)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(item_router)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)