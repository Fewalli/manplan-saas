from fastapi import FastAPI
from pythonjsonlogger import jsonlogger
import logging

from .settings import settings

app = FastAPI(title="ManPlan API", version="0.1.0")

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.handlers = [handler]

setup_logging()

@app.get("/health")
def health():
    return {"status": "ok"}