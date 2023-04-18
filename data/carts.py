import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class Cart(SqlAlchemyBase, UserMixin):
    __tablename__ = 'carts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    products = sqlalchemy.Column(sqlalchemy.VARCHAR, nullable=True, default='{}')
    amount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
