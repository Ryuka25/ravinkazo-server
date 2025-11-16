import os
import uuid
import json
from fastapi import FastAPI, WebSocket, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.models.item import Item
from app.models.experience import Experience, Picture
from app.websocket import manager
from app.schemas import Experience as ExperienceSchema, ExperienceCreate, Picture as PictureSchema
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Configure CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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
            message_data = {"event_type": "message", "event_details": data}
            await manager.broadcast(json.dumps(message_data))
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


@app.post("/experiences/", response_model=ExperienceSchema)
async def create_experience(
    firstname: str = Form(...),
    lastname: str = Form(...),
    message: str = Form(...),
    coordinates: str = Form(...),
    journeyPictures: list[UploadFile] = File(...),
    idPicture: UploadFile = File(None),
    email: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    coords = json.loads(coordinates)
    exp_data = ExperienceCreate(
        firstname=firstname,
        lastname=lastname,
        message=message,
        lat=coords["lat"],
        lon=coords["lon"],
        email=email
    )
    experience = Experience(**exp_data.dict())
    db.add(experience)
    await db.commit()
    await db.refresh(experience)

    experience_id = experience.id

    pictures = []
    for file in journeyPictures:
        file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        picture = Picture(path=file_path, experience_id=experience_id)
        pictures.append(picture)

    if idPicture:
        file_path = f"uploads/{uuid.uuid4()}_{idPicture.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(idPicture.file.read())
        picture = Picture(
            path=file_path, experience_id=experience_id, is_id_picture=1
        )
        pictures.append(picture)

    db.add_all(pictures)
    await db.commit()

    # Re-fetch the experience with the pictures relationship eagerly loaded
    result = await db.execute(
        select(Experience)
        .options(selectinload(Experience.pictures))
        .filter(Experience.id == experience_id)
    )
    experience = result.scalars().first()

    # Broadcast the new experience
    if experience:
        experience_data = ExperienceSchema.model_validate(experience).model_dump()
        event_message = {
            "event_type": "experience-created",
            "event_details": experience_data
        }
        await manager.broadcast(json.dumps(event_message, default=str))

    return experience


@app.get("/experiences/", response_model=list[ExperienceSchema])
async def read_experiences(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Experience).options(selectinload(Experience.pictures)).order_by(desc(Experience.id)).offset(skip).limit(limit)
    )
    experiences = result.scalars().all()
    return experiences


@app.get("/experiences/{experience_id}", response_model=ExperienceSchema)
async def read_experience(experience_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Experience)
        .options(selectinload(Experience.pictures))
        .filter(Experience.id == experience_id)
    )
    experience = result.scalars().first()
    return experience