import os
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///data/pricelens.db"

# For SQLite allow multithreaded access
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TrackedItem(Base):
    __tablename__ = "tracked_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)    # Telegram user id or Whatsapp phone
    platform = Column(String, nullable=False)  # amazon / flipkart
    product_id = Column(String, nullable=True) # ASIN or Flipkart id
    title = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    affiliate_url = Column(Text, nullable=True)
    current_price = Column(Numeric, nullable=True)
    lowest_price = Column(Numeric, nullable=True)
    highest_price = Column(Numeric, nullable=True)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

# DB helper functions
def add_tracked_item(user_id, platform, product_id, title, image_url, affiliate_url, price):
    db = SessionLocal()
    try:
        item = TrackedItem(
            user_id=str(user_id),
            platform=platform,
            product_id=product_id,
            title=title,
            image_url=image_url,
            affiliate_url=affiliate_url,
            current_price=price,
            lowest_price=price,
            highest_price=price
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()

def list_tracked_items(user_id):
    db = SessionLocal()
    try:
        items = db.query(TrackedItem).filter(TrackedItem.user_id==str(user_id)).all()
        return items
    finally:
        db.close()

def remove_tracked_item(user_id, item_id):
    db = SessionLocal()
    try:
        item = db.query(TrackedItem).filter(TrackedItem.user_id==str(user_id), TrackedItem.id==int(item_id)).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
    finally:
        db.close()

def update_prices(item_id, new_price):
    db = SessionLocal()
    try:
        item = db.query(TrackedItem).filter(TrackedItem.id==int(item_id)).first()
        if not item:
            return None
        changed = False
        if new_price is not None:
            if item.current_price is None or new_price != float(item.current_price):
                item.current_price = new_price
                if item.lowest_price is None or new_price < float(item.lowest_price):
                    item.lowest_price = new_price
                if item.highest_price is None or new_price > float(item.highest_price):
                    item.highest_price = new_price
                changed = True
        item.last_checked = datetime.datetime.utcnow()
        db.add(item)
        db.commit()
        db.refresh(item)
        return item, changed
    finally:
        db.close()