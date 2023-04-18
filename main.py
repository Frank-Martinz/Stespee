from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user
from forms.loginform import LoginForm
from forms.registform import RegistrationForm
from data import db_session
from data.users import User
from data.products import Product

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pfybvfqntcmcgjhnfvvfkmxbrbbltdjxrb'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


def main():
    db_session.global_init("db/all_info.db")
    app.run()


@app.route('/')
@app.route('/catalog')
def first_page():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).all()
    items = list()
    for prod in products:
        items.append([prod, url_for('static', filename=prod.image)])
    return render_template('catalog.html', items=items)


@app.route('/catalog/<category>')
def catalog_by_category(category):
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.category == category).all()
    items = list()
    for prod in products:
        items.append([prod, url_for('static', filename=prod.image)])
    return render_template('catalog.html', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', form=form, message='Неверно введён логин или пароль')
    return render_template('login.html', form=form)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.repeat_password.data:
            return render_template('registration.html', form=form, message='Пароли не совпадают')
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.login == form.email.data).first():
            return render_template('registration.html', form=form,
                                   message='Пользователь с такой электронной почтой уже существует')
        user = User(
            login=form.email.data,
            name=form.name.data,
            surname=form.surname.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/')
    return render_template('registration.html', form=form)


@app.route('/product/<int:id>', methods=['GET', 'POST'])
def show_the_product(id):
    if request.method == 'GET':
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id).first()
    else:
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id).first()

    raiting = []
    if int(product.raiting) != product.raiting:
        for i in range(int(product.raiting)):
            raiting.append('star')
        raiting.append('star-half')
        if 5 - int(product.raiting) > 1:
            for i in range(5 - int(product.raiting)):
                raiting.append('star-outline')
    else:
        for i in range(int(product.raiting)):
            raiting.append('star')
        if 5 - int(product.raiting) > 0:
            for i in range(5 - int(product.raiting)):
                raiting.append('star-outline')

    return render_template('product.html', item=product, image=url_for('static', filename=product.image),
                           raiting=raiting)


@app.route('/account/<int:id>')
def show_account():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    return render_template('account.html', item=user)


if __name__ == '__main__':
    main()
