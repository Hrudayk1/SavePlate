from fastapi import FastAPI
from routes import users, listings
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(listings.router)
