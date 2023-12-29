from . import db
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List


class HotelSearchKeys(db.Model):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    search_text: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    children: Mapped[List["HotelInfo"]] = relationship(
        backref="searchkey", lazy="dynamic", cascade="all, delete")

    def __init__(self, search_text, base_url):
        self.search_text = search_text
        self.base_url = base_url


class HotelInfo(db.Model):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    search_key: Mapped[int] = mapped_column(Integer, ForeignKey(
        "hotel_search_keys.id"), nullable=False)
    hotel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    address: Mapped[str] = mapped_column(String(1000), nullable=True)
    phone: Mapped[str] = mapped_column(String(255), nullable=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now)

    def __init__(self, search_id, hotel_name, url, address, phone):
        self.search_key = search_id
        self.hotel_name = hotel_name
        self.url = url
        self.address = address
        self.phone = phone


class LogDetails(db.Model):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50))
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now)

    def __init__(self, message, status):
        self.message = message
        self.status = status


class SearchQueue(db.Model):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    search_text: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ONGOING")
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now)

    def __init__(self, search_text):
        self.search_text = search_text
