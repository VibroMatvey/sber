from fastapi import FastAPI, Depends, Form, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from db import SessionLocal, engine, schemas, models
from fastapi.security import OAuth2PasswordRequestForm
from service.account import login_sber, sms_confirmation_sber, data_sber, create_account, get_account, get_accounts, \
    update_account_data, update_account_photo
from service.auth import token, get_current_active_user, verify_password
from service.card import create_card, delete_card, update_card_data, create_card_status, delete_card_status
from service.place import get_places, create_places, delete_place
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.mount("/static", StaticFiles(directory="static/photos"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def startup_event():
    db = SessionLocal()
    db.query(models.Account).filter(models.Account.status == "Синхронизация").update({
        "status": "Требуется авторизация"
    })
    db.commit()
    user = db.query(models.User).filter(models.User.login == 'user').first()
    if user:
        return user
    else:
        user = models.User(
            login='user',
            password='$2y$10$kgLBoPDWJdORJOwonvP3SuyrP8YZGoovIwOf1Lid84YEyGFMGihO2'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db)
):
    return await token(form_data, db)


@app.get('/accounts', response_model=list[schemas.Account])
async def accounts_get(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await get_accounts(db, current_user.id)


@app.delete('/accounts/{account_id}')
async def accounts_get(
        account_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if account:
        result = db.query(models.Account).filter(models.Account.id == account_id).delete()
        db.commit()
        return result
    raise HTTPException(404, {
        "message": "Card status not found"
    })


@app.get('/accounts/{account_id}', response_model=schemas.Account)
async def accounts_get(
        account_id: str,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await get_account(db, account_id, current_user.id)


@app.patch("/accounts/{account_id}")
async def edit_account_photo(
        account_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        account: schemas.AccountUpdate,
        db: Session = Depends(get_db)
):
    item = db.query(models.Account).filter(models.Account.id == account_id).first()
    if item:
        update_data = account.model_dump(exclude_unset=True)
        return await update_account_data(update_data, account_id, db)
    raise HTTPException(404, {
        "message": "account not found"
    })


@app.patch("/accounts/photo/{account_id}")
async def edit_account_photo(
        account_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        photo: Annotated[UploadFile, File],
        db: Session = Depends(get_db)
):
    item = db.query(models.Account).filter(models.Account.id == account_id).first()
    if item:
        return await update_account_photo(photo, item, db)
    raise HTTPException(404, {
        "message": "account not found"
    })


@app.post("/accounts")
async def accounts_create(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        login: Annotated[str, Form()],
        password: Annotated[str, Form()],
        name: Annotated[str, Form()],
        place: Annotated[str, Form()],
        code: Annotated[str, Form()],
        db: Session = Depends(get_db)
):
    return await create_account(account={
        "login": login,
        "password": password,
        "name": name,
        "place": place,
        "code": code,
        "user_id": current_user.id,
    }, db=db)


@app.post("/login")
async def login_account(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        background_tasks: BackgroundTasks,
        account: schemas.AccountLogin,
        db: Session = Depends(get_db)
):
    acc = db.query(models.Account).where(models.Account.login == account.login).first()
    if acc.status == "Синхронизация" or acc.status == "СМС подтверждение" or acc.status == "Синхронизирован":
        raise HTTPException(405, {
            "message": "driver not found"
        })
    if not acc:
        raise HTTPException(404, {
            "message": "account not found"
        })
    if not verify_password(account.password, acc.password):
        raise HTTPException(404, {
            "message": "account not found"
        })
    db.query(models.Account).where(models.Account.login == account.login).update({
        "status": "Синхронизация"
    })
    db.commit()
    background_tasks.add_task(login_sber, account, db)
    return {
        "ok"
    }


@app.post("/sms")
async def sms_confirmation(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        account: schemas.AccountSms,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    acc = db.query(models.Account).filter(models.Account.login == account.login).first()
    if acc.status == "Синхронизация":
        raise HTTPException(405, {
            "message": "driver not found"
        })
    db.query(models.Account).filter(models.Account.login == account.login).update({
        "status": 'Синхронизация'
    })
    db.commit()
    background_tasks.add_task(sms_confirmation_sber, account, db)
    return {
        'ok'
    }


@app.post("/data")
async def data(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        account: schemas.AccountData,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    acc = db.query(models.Account).filter(models.Account.login == account.login).first()
    if acc.status == "Синхронизация":
        raise HTTPException(405, {
            "message": "driver not found"
        })
    db.query(models.Account).filter(models.Account.login == account.login).update({
        "status": 'Синхронизация'
    })
    db.commit()
    background_tasks.add_task(data_sber, account, db)
    return {
        'ok'
    }


@app.post("/places", response_model=schemas.Place)
async def create_place(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        place: schemas.PlaceCreate,
        db: Session = Depends(get_db)
):
    return await create_places(place=place, db=db)


@app.get("/places", response_model=list[schemas.Place])
async def get_all_places(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await get_places(db=db)


@app.delete("/places/{place_id}")
async def delete_place_by_id(
        place_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await delete_place(place_id=place_id, db=db)


@app.post("/cards", response_model=schemas.Place)
async def create_place(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        card: schemas.CardCreate,
        db: Session = Depends(get_db)
):
    return await create_card(card=card, db=db)


@app.delete("/cards/{card_id}")
async def delete_place_by_id(
        card_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await delete_card(card_id=card_id, db=db)


@app.patch("/cards/{card_id}")
async def edit_account_photo(
        card_id: int,
        card: schemas.CardUpdate,
        db: Session = Depends(get_db)
):
    item = db.query(models.Cards).filter(models.Cards.id == card_id).first()
    if item:
        update_data = card.model_dump(exclude_unset=True)
        return await update_card_data(update_data, card_id, db)
    raise HTTPException(404, {
        "message": "card not found"
    })


@app.post("/cards/status", response_model=schemas.CardStatus)
async def create_place(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        card: schemas.CardStatusCreate,
        db: Session = Depends(get_db)
):
    return await create_card_status(card=card, db=db)


@app.delete("/cards/status/{status_id}")
async def delete_place_by_id(
        status_id: int,
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return await delete_card_status(status_id=status_id, db=db)


@app.get("/cards/status", response_model=list[schemas.CardStatus])
async def get_all_places(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: Session = Depends(get_db)
):
    return db.query(models.CardsStatus).all()
