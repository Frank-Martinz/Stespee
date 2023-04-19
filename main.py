from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, current_user, logout_user
from forms.loginform import LoginForm
from forms.registform import RegistrationForm
from forms.changingform import ChangingForm_login, ChangingForm_surname, ChangingForm_name, ChangingForm_password
from data import db_session
from data.users import User
from data.products import Product
from data.carts import Cart

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
    db_sess.close()
    return render_template('catalog.html', items=items)


@app.route('/catalog/<category>')
def catalog_by_category(category):
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.category == category).all()
    items = list()
    for prod in products:
        items.append([prod, url_for('static', filename=prod.image)])
    db_sess.close()
    return render_template('catalog.html', items=items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.login == form.login.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect("/")
        db_sess.close()
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
        db_sess.close()
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
    db_sess.close()
    return render_template('product.html', item=product, image=url_for('static', filename=product.image),
                           raiting=raiting)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/cart')
def cart():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user_cart = db_sess.query(Cart).filter(Cart.user_id == current_user.id).first()
        if user_cart.products == '{}':
            return render_template('cart.html', show_smth=False)
        else:
            print(user_cart.products)
            prods = create_dict_of_prod(user_cart.products)
            products = db_sess.query(Product).filter(Product.id.in_(list(prods.keys()))).all()
            amount = count_whole_cost(prods)
            items = []
            for item in products:
                items.append([current_user.id, prods[item.id], item, url_for('static', filename=item.image)])
            db_sess.close()
            return render_template('cart.html', items=items, show_smth=True, amount=amount)
    else:
        return redirect('/login')


@app.route('/account')
def account():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(current_user.id == User.id).first()
    db_sess.close()
    return render_template('account.html', item=user)


@app.route('/add/<int:user_id>/<int:product_id>/<int:tp>', methods=['POST'])
def add(user_id, product_id, tp):
    db_sess = db_session.create_session()
    user_cart = db_sess.query(Cart).filter(Cart.user_id == user_id).first()
    if user_cart.products == '{}':
        prods = {}
    else:
        prods = create_dict_of_prod(user_cart.products)
    if not (product_id in prods):
        prods[product_id] = 1
    else:
        prods[product_id] += 1
    amount = count_whole_cost(prods)
    user_cart.products = str(prods)
    user_cart.amount = int(amount)
    db_sess.commit()
    db_sess.close()
    if tp == 1:
        return redirect('/cart')
    return redirect(f'/product/{product_id}')


@app.route('/minus/<int:user_id>/<int:product_id>', methods=['POST'])
def minus(user_id, product_id):
    db_sess = db_session.create_session()
    user_cart = db_sess.query(Cart).filter(Cart.user_id == user_id).first()
    prods = create_dict_of_prod(user_cart.products)
    prods[product_id] -= 1
    if prods[product_id] == 0:
        prods.pop(product_id)
    amount = count_whole_cost(prods)
    user_cart.products = str(prods)
    user_cart.amount = int(amount)
    db_sess.commit()
    db_sess.close()
    return redirect('/cart')


@app.route('/change_info/<tp>', methods=['GET', 'POST'])
def change_info(tp):
    if tp == 'login':
        form = ChangingForm_login()
    elif tp == 'password':
        form = ChangingForm_password()
    elif tp == 'name':
        form = ChangingForm_name()
    elif tp == 'surname':
        form = ChangingForm_surname()
    else:
        return redirect('/account')

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if tp == 'login':
            user.login = form.login.data
        elif tp == 'password':
            user.password = form.password.data
        elif tp == 'name':
            user.name = form.name.data
        elif tp == 'surname':
            user.surname = form.surname.data
        db_sess.commit()
        db_sess.close()
        return redirect('/account')
    return render_template('change_info.html', form=form, tp=tp)


def create_dict_of_prod(products: str):
    products = products[1:-1]
    if ', ' in products:
        prods = products.split(', ')
        a = dict()
        for prod in prods:
            pp = prod.split(': ')
            a[int(pp[0])] = int(pp[1])
    else:
        a = dict()
        pp = products.split(': ')
        a[int(pp[0])] = int(pp[1])
    return a


def count_whole_cost(prods_in_cart):
    db_sess = db_session.create_session()
    amount = 0
    for key in prods_in_cart:
        result = db_sess.query(Product).filter(Product.id == key).first()
        amount += result.cost * prods_in_cart[key]
    db_sess.close()
    return amount


if __name__ == '__main__':
    main()
