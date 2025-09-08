import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text, Boolean, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL in .env (postgres connection for Supabase)")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    name = Column(String, nullable=True)
    platform = Column(String)
    location_area_code = Column(String, nullable=True)
    ref_code = Column(String, nullable=True)
    referred_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    product_id = Column(String, nullable=True, index=True)
    user_id = Column(String, index=True)
    url = Column(Text)
    platform = Column(String)
    product_name = Column(Text)
    image_url = Column(Text)
    current_price = Column(Numeric)
    prev_price = Column(Numeric, nullable=True)
    lowest_price = Column(Numeric, nullable=True)
    highest_price = Column(Numeric, nullable=True)
    affiliate_link = Column(Text, nullable=True)
    last_checked = Column(DateTime, default=func.now())
    tracking_status = Column(String, default="active")


class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Numeric)
    checked_at = Column(DateTime, default=func.now())


class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    message = Column(Text)
    link = Column(Text, nullable=True)
    platform = Column(String, nullable=True)
    area_code = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()