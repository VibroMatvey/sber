from fastapi import HTTPException

from db import engine, schemas, models


async def create_card(card, db):
    db_card = models.Cards(
        title=card.title,
        status=card.status,
        account_id=card.account_id,
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


async def create_card_status(card, db):
    db_card_status = models.CardsStatus(
        title=card.title,
    )
    db.add(db_card_status)
    db.commit()
    db.refresh(db_card_status)
    return db_card_status


async def delete_card(card_id: int, db):
    card = db.query(models.Cards).filter(models.Cards.id == card_id).first()
    if card:
        result = db.query(models.Cards).filter(models.Cards.id == card_id).delete()
        db.commit()
        return result
    raise HTTPException(404, {
        "message": "Card not found"
    })


async def delete_card_status(status_id: int, db):
    card = db.query(models.CardsStatus).filter(models.CardsStatus.id == status_id).first()
    if card:
        result = db.query(models.CardsStatus).filter(models.CardsStatus.id == status_id).delete()
        db.commit()
        return result
    raise HTTPException(404, {
        "message": "Card status not found"
    })


async def update_card_data(data, card_id, db):
    db.query(models.Cards).filter(models.Cards.id == card_id).update(data)
    db.commit()
    return HTTPException(200, {
        "message": "successful update"
    })
