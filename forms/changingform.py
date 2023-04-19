from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class ChangingForm_login(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ChangingForm_password(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ChangingForm_name(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Изменить')


class ChangingForm_surname(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired()])
    submit = SubmitField('Изменить')
