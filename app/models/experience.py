import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, index=True)
    lastname = Column(String, index=True)
    message = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    email = Column(String, nullable=True)
    added_date = Column(DateTime, default=datetime.datetime.utcnow)
    pictures = relationship("Picture", back_populates="experience")


class Picture(Base):
    __tablename__ = "pictures"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True)
    experience_id = Column(Integer, ForeignKey("experiences.id"))
    is_id_picture = Column(Integer, default=0)
    experience = relationship("Experience", back_populates="pictures")
