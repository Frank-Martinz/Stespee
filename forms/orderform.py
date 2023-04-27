from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class OrderForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    phone_number = StringField('Номер телефона', validators=[DataRequired()])
    address = StringField('Адрес доставки', validators=[DataRequired()])
    submit = SubmitField('Перейти к оплате')