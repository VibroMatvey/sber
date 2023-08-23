from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship, mapped_column
from .database import Base
import json

report_data = json.dumps([
    {
        "label": 'ФИО',
        "value": ''
    },
    {
        "label": 'Дата рождения',
        "value": ''
    },
    {
        "label": 'ПИН-код',
        "value": ''
    },
    {
        "label": 'Новый номер телефона',
        "value": ''
    },
    {
        "label": 'Последнее посещение сбербанка (дата, адрес)',
        "value": ''
    },
    {
        "label": 'На какой телефон установлен сбер',
        "value": ''
    },
    {
        "label": 'Старый номер телефона',
        "value": ''
    },
    {
        "label": 'Есть кредиты, кредитки, займы',
        "value": ''
    },
    {
        "label": 'Какими сервисами такси или каршеринга часто пользовались?',
        "value": ''
    },
    {
        "label": 'Где в последний раз снимали деньги',
        "value": ''
    },
    {
        "label": 'Знак зодиака',
        "value": ''
    },
    {
        "label": 'Электронная почта',
        "value": ''
    },
    {
        "label": 'Полных лет',
        "value": ''
    },
    {
        "label": 'Сотовый оператор',
        "value": ''
    },
    {
        "label": 'Сколько этажей по прописке',
        "value": ''
    },
    {
        "label": 'Кому были частые переводы',
        "value": ''
    },
    {
        "label": 'Есть ли ежемесячные поступления(пособия, зп)',
        "value": ''
    },
    {
        "label": 'Где часто совершаете покупки',
        "value": ''
    },
    {
        "label": 'Где получали паспорт (адрес)',
        "value": ''
    },
    {
        "label": 'Где получали карту (дата, адрес)',
        "value": ''
    },
    {
        "label": 'Адрес регистрации по паспорту',
        "value": ''
    },
    {
        "label": 'Девичья фамилия матери',
        "value": ''
    },
])


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True)
    password = Column(String)
    disabled = Column(Boolean, nullable=True)
    accounts = relationship("Account", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    photos = Column(String)
    place = Column(String)
    code = Column(String)
    login = Column(String, unique=True)
    password = Column(String)
    number = Column(String, nullable=True)
    fullname = Column(String, nullable=True)
    address = Column(String, nullable=True)
    bill = Column(String, default='0')
    cards_count = Column(String, nullable=True)
    day_limit = Column(String, nullable=True)
    cards_details = Column(String, nullable=True)
    report = Column(String, default=report_data)
    status = Column(String, default='Требуется авторизация')
    date = Column(String, nullable=True)
    user_id = Column('user_id', Integer(), ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="accounts")
    cards = relationship("Cards", back_populates="account")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)


class Cards(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    status = Column(String)
    account_id = Column('account_id', Integer(), ForeignKey('accounts.id'), nullable=False)
    account = relationship("Account", back_populates="cards")


class CardsStatus(Base):
    __tablename__ = "cards_status"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
