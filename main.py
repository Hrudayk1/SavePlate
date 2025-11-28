from fastapi import FastAPI
from routes import users, listings, orders, negotiations, notifications, payment, charity, donate, chat, ratings
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(listings.router)
app.include_router(orders.router)
app.include_router(negotiations.router)
app.include_router(notifications.router)
app.include_router(payment.router)
app.include_router(charity.router)
app.include_router(donate.router)
app.include_router(chat.router)
app.include_router(ratings.router)