"""Core ORM models: users → farms → fields → devices → readings"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.config.database import Base

def _uuid():
    return uuid.uuid4().hex[:12]

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="farmer")
    created_at = Column(DateTime, default=datetime.utcnow)

    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan")

class Farm(Base):
    __tablename__ = "farms"
    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="My Farm")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="farms")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")

class Field(Base):
    __tablename__ = "fields"
    id = Column(String, primary_key=True)  # e.g. FIELD_001 or uuid
    farm_id = Column(String, ForeignKey("farms.id"), nullable=False, index=True)
    name = Column(String, default="Field 1")
    crop = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm", back_populates="fields")
    devices = relationship("Device", back_populates="field", cascade="all, delete-orphan")
    readings = relationship("SensorReading", back_populates="field")

class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)  # AGRO_NODE_001
    field_id = Column(String, ForeignKey("fields.id"), nullable=False, index=True)
    device_key_hash = Column(String, nullable=True)  # hashed device key for ingest auth
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    field = relationship("Field", back_populates="devices")
    readings = relationship("SensorReading", back_populates="device")

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False, index=True)
    field_id = Column(String, ForeignKey("fields.id"), nullable=False, index=True)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    soil_ph = Column(Float, nullable=True)
    rain = Column(Boolean, default=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="readings")
    field = relationship("Field", back_populates="readings")
