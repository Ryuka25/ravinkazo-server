from pydantic import BaseModel
import datetime


class PictureBase(BaseModel):
    path: str
    is_id_picture: int


class PictureCreate(PictureBase):
    pass


class Picture(PictureBase):
    id: int
    experience_id: int

    class Config:
        orm_mode = True


class ExperienceBase(BaseModel):
    firstname: str
    lastname: str
    message: str
    lat: float
    lon: float
    email: str | None = None


class ExperienceCreate(ExperienceBase):
    pass


class Experience(ExperienceBase):
    id: int
    added_date: datetime.datetime
    email: str | None = None
    pictures: list[Picture] = []

    class Config:
        orm_mode = True
