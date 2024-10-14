from fastapi import FastAPI

app = FastAPI()

from app import models, schemas, services, utils