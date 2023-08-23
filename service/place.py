from fastapi import HTTPException

from db import engine, schemas, models


async def get_places(db):
    return db.query(models.Place).all()


async def create_places(place, db):
    db_place = models.Place(
        title=place.title,
    )
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place


async def delete_place(place_id: int, db):
    place = db.query(models.Place).filter(models.Place.id == place_id).first()
    if place:
        result = db.query(models.Place).filter(models.Place.id == place_id).delete()
        db.commit()
        return result
    raise HTTPException(404, {
        "message": "place not found"
    })
