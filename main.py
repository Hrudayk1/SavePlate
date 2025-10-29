# main.py
from fastapi import FastAPI
from database import Base, engine
from routes import users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SavePlate API")

app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "SavePlate backend running!"}
