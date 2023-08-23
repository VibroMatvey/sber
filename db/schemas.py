from typing import Annotated, List, Optional

from fastapi import Form, UploadFile, File
from pydantic import BaseModel


class UserCreate(BaseModel):
    login: str
    password: str


class UserLogin(BaseModel):
    login: str
    password: str


class User(BaseModel):
    id: int
    login: str
    password: str


class AccountLogin(BaseModel):
    login: str
    password: str


class AccountData(BaseModel):
    login: str


class AccountSms(BaseModel):
    login: str
    sms: str


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    place: Optional[str] = None
    code: Optional[str] = None
    report: Optional[str] = None


class AccountCards(BaseModel):
    id: int
    title: str
    status: str

    class Config:
        orm_mode = True


class Account(BaseModel):
    id: int
    name: str
    photos: list[str] | None | str = []
    place: str
    code: str
    login: str
    number: str | None = None
    fullname: str | None = None
    bill: str | None = None
    cards_count: str | None = None
    day_limit: str | None = None
    address: str | None = None
    cards_details: str | None = None
    report: str | None = None
    status: str
    date: str | None = None
    user_id: int
    cards: list[AccountCards]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: str | None = None


class Place(BaseModel):
    id: int
    title: str


class PlaceCreate(BaseModel):
    title: str


class CardCreate(BaseModel):
    title: str
    status: str
    account_id: int


class CardUpdate(BaseModel):
    status: Optional[str] = None


class CardStatusCreate(BaseModel):
    title: str


class CardStatus(BaseModel):
    id: int
    title: str
