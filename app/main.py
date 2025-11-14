from fastapi import FastAPI, WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.models.item import Item
from app.websocket import manager


app = FastAPI()


# Dependency
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client says: {data}")
    except Exception:
        manager.disconnect(websocket)


@app.post("/items/")
async def create_item(name: str, description: str, db: AsyncSession = Depends(get_db)):
    item = Item(name=name, description=description)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    items = await db.execute(Item.__table__.select().offset(skip).limit(limit))
    return items.fetchall()