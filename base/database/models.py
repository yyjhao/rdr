from sqlalchemy import Column, ForeignKey, Index, Table
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy import Integer, String, DateTime, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import \
    ARRAY, BIGINT, BIT, BOOLEAN, BYTEA, CHAR, CIDR, DATE, \
    DOUBLE_PRECISION, ENUM, FLOAT, HSTORE, INET, INTEGER, \
    INTERVAL, JSON, MACADDR, NUMERIC, REAL, SMALLINT, TEXT, \
    TIME, TIMESTAMP, UUID, VARCHAR, INT4RANGE, INT8RANGE, NUMRANGE, \
    DATERANGE, TSRANGE, TSTZRANGE, TSVECTOR
from base.database.session import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    info = Column(JSON)
    email = Column(String(255), index=True, unique=True)


class UserClassifier(Base):
    __tablename__ = 'user_classifier'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), index=True, unique=True)
    classifier = Column(BYTEA, nullable=False)
    locked = Column(DateTime, nullable=True)


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    info = Column(JSON, nullable=False)
    type = Column(String(255), nullable=False)
    ext_uid = Column(String(512), index=True, nullable=False, unique=True)
    last_retrive = Column(DateTime, nullable=True)
    is_private = Column(BOOLEAN, nullable=False)


user_source = Table('user_source', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('source_id', Integer, ForeignKey('source.id')),
    Column('last_append_id', Integer, nullable=True),
)


class UserUrl(Base):
    __tablename__ = 'user_url'
    __table_args__ = (
        Index('user_url_index', "user_id", "url_id"),
        UniqueConstraint('user_id', 'url_id', name='user_single_url'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), index=True)
    url_id = Column(Integer, ForeignKey('url.id'), index=True)
    score = Column(Integer, index=True)
    last_action = Column(String, index=True)
    last_action_timestamp = Column(DateTime, index=True)
    articles = Column(MutableDict.as_mutable(HSTORE))


class Url(Base):
    __tablename__ = 'url'

    id = Column(Integer, primary_key=True)
    url = Column(String(512), unique=True, index=True)


class Origin(Base):
    __tablename__ = 'origin'

    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), nullable=False, index=True, unique=True)
    display_name = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    timestamp = Column(DateTime, nullable=False, index=True)
    origin_id = Column(Integer, ForeignKey('origin.id'))
    image_url = Column(String(512), nullable=True)
    source_id = Column(Integer, ForeignKey('source.id'))

    origin = relationship('Origin')
    url = relationship('Url')

ALL_ACTIONS = ['like', 'dislike', 'pass', 'defer']
