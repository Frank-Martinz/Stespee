import sqlalchemy
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class Feedback(SqlAlchemyBase, UserMixin):
    __tablename__ = 'feedbacks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    product_id = sqlalchemy.Column(sqlalchemy.Integer)
    feedback_text = sqlalchemy.Column(sqlalchemy.String)
    mark = sqlalchemy.Column(sqlalchemy.Integer)
    user_name = sqlalchemy.Column(sqlalchemy.String)
