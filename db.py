from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
from sqlalchemy.types import UserDefinedType
from sqlalchemy.dialects.postgresql import JSON, ENUM as PGEnum


config = Config()
DATABASE_URL = config.DATABASE_URL

# Create engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class VectorType(UserDefinedType):
    def get_col_spec(self, **kwargs):
        # Specify the dimension here (e.g., VECTOR(2560) for 2560 dimensions)
        return "VECTOR(2560)"

    def bind_expression(self, bindvalue):
        return bindvalue

    def column_expression(self, col):
        return col

class WebsiteEmbedding(Base):
    __tablename__ = "website_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(VectorType, nullable=False)  # Assuming VectorType is correctly defined
    keywords = Column(JSON, nullable=False)  # Store keywords as JSON, adjust as needed

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # session_id
    message_type = Column(PGEnum("user", "assistant", name="message_type_enum"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)  # Optionally store a timestamp

# Initialize the database (for creating tables)
def init_db():
    Base.metadata.create_all(bind=engine)
