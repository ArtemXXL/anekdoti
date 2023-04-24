import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase

from sqlalchemy import orm


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    vote = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    password = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    role = sqlalchemy.Column(sqlalchemy.String, default="regular")
    is_photo = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


class Joke(SqlAlchemyBase):
    __tablename__ = 'jokes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    range = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)



