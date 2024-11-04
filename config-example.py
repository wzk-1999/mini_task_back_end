# config.py
class Config:
    DEBUG = True # turn false when you deploy to production env
    DB_TYPE = "postgres"
    DB_USER = "your db user"
    DB_PASSWORD = "your db password"
    DB_HOST = "your db host"
    DB_PORT = "your db port"
    DB_NAME = "your db name"

    #----------------embedding model--------------------------

    ARK_API_KEY = "your embedding api key"
    ARK_MODEL = "your embedding model"
    ARK_API_LINK = "your embedding model api link" # for Volcano Ark provider is using sdk not api
    # ----------------chat model-----------------------------------
    LLM_API_URL = "your llm api url"
    LLM_API_KEY = "chat llm api key"

    API_LINK_GET_CONVERSATION_ID = "api link to get conversation id"

    @property
    def DATABASE_URL(self):
        return f"{self.DB_TYPE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
