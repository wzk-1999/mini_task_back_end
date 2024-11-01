from sqlalchemy.orm import sessionmaker

from config import Config
from db import engine, Base, ChatHistory

config = Config()
DATABASE_URL = config.DATABASE_URL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist yet
Base.metadata.create_all(bind=engine)

def store_message(user_id, content, message_type):
    """Stores a message in the chat_history table with the given user_id, content, and message type."""
    db = SessionLocal()
    try:
        message = ChatHistory(user_id=user_id, content=content, message_type=message_type)
        db.add(message)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_chat_history(user_id):
    """Retrieves chat history for a given user_id, returning messages as a list of dictionaries with role and content."""
    db = SessionLocal()
    try:
        # Query chat history for the given user_id
        history = db.query(ChatHistory).filter_by(user_id=user_id).order_by(ChatHistory.timestamp).all()

        # Format the result as a list of dictionaries with 'role' and 'content' keys
        chat_history = [{"role": msg.message_type, "content": msg.content} for msg in history]
        return chat_history
    except Exception as e:
        raise e
    finally:
        db.close()