import os

class Config:
    mode="prod" 
    if mode=="prod":
        APP_BASE_URL = os.getenv("APP_BASE_URL", "https://www.backend.scientiflow.com/api")
    elif mode=="dev":
        APP_BASE_URL = "http://127.0.0.1:8000/api"
        # APP_BASE_URL = os.getenv("APP_BASE_URL", "https://www.scientiflow-backend-dev.scientiflow.com/api")        