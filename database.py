from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import config

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    username = Column(String(255))
    language = Column(String(10), default='en')
    is_banned = Column(Boolean, default=False)
    is_gbanned = Column(Boolean, default=False)
    warns = Column(Integer, default=0)
    join_date = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    sudo = Column(Boolean, default=False)
    
class Chats(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(String(255))
    type = Column(String(50))  # private, group, supergroup, channel
    welcome = Column(Text)
    goodbye = Column(Text)
    rules = Column(Text)
    welcome_enabled = Column(Boolean, default=True)
    goodbye_enabled = Column(Boolean, default=True)
    clean_welcome = Column(Boolean, default=False)
    clean_goodbye = Column(Boolean, default=False)
    clean_service = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    lock_types = Column(JSON, default=list)
    fed_id = Column(String(100))
    antispam = Column(Boolean, default=True)
    antispam_action = Column(String(50), default='mute')
    captcha = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
class Filters(Base):
    __tablename__ = 'filters'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    keyword = Column(String(255), nullable=False)
    reply = Column(Text, nullable=False)
    is_document = Column(Boolean, default=False)
    is_image = Column(Boolean, default=False)
    is_audio = Column(Boolean, default=False)
    is_voice = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    has_buttons = Column(Boolean, default=False)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now)

class Notes(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_document = Column(Boolean, default=False)
    is_image = Column(Boolean, default=False)
    is_audio = Column(Boolean, default=False)
    is_voice = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    has_buttons = Column(Boolean, default=False)
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now)

class Warns(Base):
    __tablename__ = 'warns'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    reason = Column(Text)
    warned_by = Column(BigInteger)
    warned_at = Column(DateTime, default=datetime.now)

class Federations(Base):
    __tablename__ = 'federations'
    id = Column(Integer, primary_key=True)
    fed_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    owner_id = Column(BigInteger, nullable=False)
    admins = Column(JSON, default=list)
    chats = Column(JSON, default=list)
    fbans = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now)

class GBans(Base):
    __tablename__ = 'gbans'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    reason = Column(Text)
    banned_by = Column(BigInteger)
    banned_at = Column(DateTime, default=datetime.now)

class Connections(Base):
    __tablename__ = 'connections'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger)
    chat_title = Column(String(255))
    connected_at = Column(DateTime, default=datetime.now)

# Initialize database
def init_db():
    engine = create_engine(
        config.Config.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )
    Base.metadata.create_all(engine)
    return engine

engine = init_db()
Session = scoped_session(sessionmaker(bind=engine))
