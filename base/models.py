from sqlalchemy import Column, ForeignKey, Table, Index
from sqlalchemy import Integer, String, DateTime, UniqueConstraint, Text
from sqlalchemy.dialects.mysql import LONGBLOB
from base.database import Base
from sqlalchemy.orm import relationship, backref

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    ext_uid = Column(String(255), index=True)
    auth_token = Column(String(255))
    email = Column(String(255))

    def is_authenticated(self):
        return True

    @property
    def serialize(self):
       return {
           'name': self.name,
           'email': self.email,
       }

class UserClassifier(Base):
    __tablename__ = 'user_classifier'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), index=True, unique=True)
    classifier = Column(LONGBLOB, nullable=False)
    locked = Column(DateTime, nullable=True)

article_origin_table = Table('article_origin', Base.metadata,
    Column('artcile_id', Integer, ForeignKey('article.id')),
    Column('origin_id', Integer, ForeignKey('origin.id'))
)

class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), index=True)
    token = Column(String(512), nullable=False)
    type = Column(String(255), nullable=False)
    last_indicator = Column(String(255), nullable=True)
    name = Column(String(512), nullable=False)
    last_fail = Column(DateTime, nullable=True)
    ext_uid = Column(String(255), index=True, nullable=True)

    user = relationship("User", backref=backref('sources', order_by=id))

    @property
    def serialize(self):
       return {
           'id': self.id,
           'name': self.name,
           'type': self.type
       }

class Origin(Base):
    __tablename__ = 'origin'
    __table_args__ = (Index('orign_index', "identifier", "source_id"), )

    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), nullable=False, index=True)
    source_id = Column(Integer, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)

    @property
    def serialize(self):
        return {
            'display_name': self.display_name,
            'image_url': self.image_url,
        }

class Article(Base):
    __tablename__ = 'article'
    __table_args__ = (
        UniqueConstraint('url', 'user_id', name='user_url'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), index=True)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    score = Column(Integer, index=True)
    origins = relationship('Origin', secondary=article_origin_table)
    last_action = Column(String(255), nullable=True, index=True)
    last_action_timestamp = Column(DateTime, nullable=True)
    image_url = Column(String(512), nullable=True)

    @property
    def serialize(self):
        return {
            'title': self.title,
            'summary': self.summary,
            'url': self.url,
            'image_url': self.image_url,
            'id': self.id,
            'last_action_timestamp': self.last_action_timestamp,
            'origins': [o.serialize for o in self.origins]
        }

ALL_ACTIONS = ['like', 'dislike', 'pass', 'defer']
