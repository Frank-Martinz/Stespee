import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class Product(SqlAlchemyBase, UserMixin):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    cost = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    info = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    category = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    raiting = sqlalchemy.Column(sqlalchemy.Double, nullable=False)
