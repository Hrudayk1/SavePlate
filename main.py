from fastapi import FastAPI
from routes import users, listings, orders, negotiations, notifications
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(negotiations.router)
app.include_router(notifications.router)