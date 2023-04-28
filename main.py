from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_restful import Api, Resource
from werkzeug.security import generate_password_hash
from forms.loginform import LoginForm
from forms.registform import RegistrationForm
from forms.changingform import ChangingForm_login, ChangingForm_surname, ChangingForm_name, ChangingForm_password
from forms.orderform import OrderForm
from data import db_session
from data.users import User
from data.products import Product
from data.carts import Cart
from data.orders import Order
from data.feedbacks import Feedback
import re
import sys
import requests


class OrderResource(Resource):
    def post(self, apikey, order_id, new_status):
        with open('static/apikey.txt', 'r') as file:
            data = file.read()
            if data != apikey:
                return jsonify({'Error': f'Apikey is not worked'})
        db_sess = db_session.create_session()
        order = db_sess.query(Order).filter(Order.id == order_id).first()
        if order is None:
            db_sess.close()
            return jsonify({'Error': f'Not found order with id: {order_id}'})

        order.status = new_status
        db_sess.commit()
        db_sess.close()
        return jsonify({'success': 'OK'})


application = Flask(__name__)
api = Api(application)
api.add_resource(OrderResource, '/api/<apikey>/<int:order_id>/<new_status>')
application.config['SECRET_KEY'] = 'pfybvfqntcmcgjhnfvvfkmxbrbbltdjxrb'
login_manager = LoginManager()
login_manager.init_app(application)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


def main():
    db_session.global_init("db/all_info.db")
    application.run()


@application.route('/')
@application.route('/catalog')
def first_page():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).all()
    items = list()
    for prod in products:
        items.append([prod, url_for('static', filename=prod.image), count_stars(prod)])
    db_sess.close()
    return render_template('catalog.html', items=items)


@application.route('/catalog/<category>')
def catalog_by_category(category):
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.category == category).all()
    items = list()
    for prod in products:
        items.append([prod, url_for('static', filename=prod.image), count_stars(prod)])
    db_sess.close()
    return render_template('catalog.html', items=items)


@application.route('/login', methods=['GET', 'POST'])
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


@application.route('/registration', methods=['GET', 'POST'])
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
        cart = Cart(
            user_id=user.id,
            amount=0,
        )
        db_sess.add(cart)
        db_sess.commit()
        db_sess.close()
        return redirect('/')
    return render_template('registration.html', form=form)


@application.route('/product/<int:id>', methods=['GET', 'POST'])
def show_the_product(id):
    if request.method == 'GET':
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id).first()
    else:
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id).first()
    feedback_amount = product.five_stars + product.four_stars + product.three_stars \
                      + product.two_stars + product.one_star
    feedbacks = db_sess.query(Feedback).filter(Feedback.product_id == id).all()
    raiting = count_stars(product)
    db_sess.close()
    return render_template('product.html', item=product, image=url_for('static', filename=product.image),
                           raiting=raiting, feedback_amount=feedback_amount, feedbacks=reversed(feedbacks))


@application.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@application.route('/cart')
def cart():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        user_cart = db_sess.query(Cart).filter(Cart.user_id == current_user.id).first()
        if user_cart.products == '{}':
            return render_template('cart.html', show_smth=False)
        else:
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


@application.route('/account')
def account():
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(current_user.id == User.id).first()
    db_sess.close()
    return render_template('account.html', item=user, password=str('●' * user.len_of_password))


@application.route('/create_order', methods=['GET', 'POST'])
def create_orders():
    if not current_user.is_authenticated:
        return redirect('/login')
    message = ''
    db_sess = db_session.create_session()
    user_cart = db_sess.query(Cart).filter(Cart.user_id == current_user.id).first()
    if user_cart.products == '{}':
        return redirect('/cart')
    form = OrderForm()
    if form.validate_on_submit():
        correct_address = is_correct_address(form.address.data)
        correct_phone_number = is_correct_mobile_phone_number_ru(form.phone_number.data)
        if correct_phone_number and correct_address:
            add_new_order(current_user.id, form)
            db_sess.close()
            return redirect('/payment')
        else:
            if not correct_address:
                message = 'Некорректный адрес'
            else:
                message = 'Некорректный номер телефона'
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    db_sess.close()
    return render_template('create_order.html', form=form, item=user, message=message)


@application.route('/payment/', methods=['GET', 'POST'])
def payment():
    if not current_user.is_authenticated:
        return redirect('/login')
    if request.method == 'POST':
        return redirect('/show_orders')
    db_sess = db_session.create_session()
    order = db_sess.query(Order).filter(Order.user_id == current_user.id).all()
    return render_template('payment.html', order=order[-1])


@application.route('/show_orders')
def show_orders():
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    orders = db_sess.query(Order).filter(Order.user_id == current_user.id).all()
    db_sess.close()
    items = []
    if len(orders) > 0:
        show_smth = True
        for order in reversed(orders):
            order_list = create_list_of_products(order.products)
            items.append([order, order_list])
    else:
        show_smth = False
    return render_template('show_orders.html', items=items, show_smth=show_smth)


@application.route('/add_feedback/<int:prod_id>', methods=['GET', 'POST'])
def add_feedback(prod_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    if request.method == 'POST':
        if request.form['feedback'] == '':
            product = db_sess.query(Product).filter(Product.id == prod_id).first()
            item = [product, url_for('static', filename=product.image)]
            raiting = count_stars(product)
            db_sess.close()
            return render_template('feedbackadding.html', item=item, raiting=raiting,
                                   message='Напишите пару слов о товаре')
        mark = int(request.form['mark'])
        feedback = Feedback(
            product_id=prod_id,
            feedback_text=request.form['feedback'],
            mark=mark,
            user_name=f'{current_user.name} {current_user.surname}'
        )
        db_sess.add(feedback)
        adjust_raiting(prod_id, mark, db_sess)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/product/{prod_id}')
    product = db_sess.query(Product).filter(Product.id == prod_id).first()
    item = [product, url_for('static', filename=product.image)]
    raiting = count_stars(product)
    db_sess.close()
    return render_template('feedbackadding.html', item=item, raiting=raiting)


@application.route('/add/<int:user_id>/<int:product_id>/<int:tp>', methods=['POST'])
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


@application.route('/minus/<int:user_id>/<int:product_id>', methods=['POST'])
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


@application.route('/change_info/<tp>', methods=['GET', 'POST'])
def change_info(tp):
    if not current_user.is_authenticated:
        return redirect('/login')
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
            if form.password.data == form.repeat_password.data:
                user.hashed_password = generate_password_hash(form.password.data)
                user.len_of_password = len(form.password.data)
            else:
                return render_template('change_info.html', form=form, tp=tp, message='Пароли не совпадают')
        elif tp == 'name':
            user.name = form.name.data
        elif tp == 'surname':
            user.surname = form.surname.data
        db_sess.commit()
        db_sess.close()
        return redirect('/account')
    return render_template('change_info.html', form=form, tp=tp)


def add_new_order(user_id: int, form):
    db_sess = db_session.create_session()
    user_cart = db_sess.query(Cart).filter(Cart.user_id == user_id).first()
    products = create_dict_of_prod(user_cart.products)
    text_products = ''
    for index in products:
        product = db_sess.query(Product).filter(Product.id == index).first()
        text_products += f'{product.name} x {products[index]}|'
    order = Order(
        user_id=user_cart.user_id,
        products=text_products,
        address=form.address.data,
        status='Ожидает оплаты',
        phone_number=form.phone_number.data,
        amount=user_cart.amount
    )
    db_sess.add(order)
    user_cart.products = '{}'
    db_sess.commit()
    db_sess.close()


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


def is_correct_mobile_phone_number_ru(phone_number):
    remainder = ''
    if phone_number.startswith('+7'):
        remainder = phone_number[2:]
    elif phone_number.startswith('8'):
        remainder = phone_number[1:]
    else:
        return False

    remainder = re.sub(r'[ -]', '', remainder)

    if re.match(r'^\(\d{3}\)', remainder):
        remainder = re.sub(r'\(', '', remainder, 1)
        remainder = re.sub(r'\)', '', remainder, 1)

    return bool(re.match(r'^\d{10}$', remainder))


def is_correct_address(address):
    server = 'https://search-maps.yandex.ru/v1/'
    params = {
        'apikey': 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3',
        'text': address,
        'lang': 'ru'
    }
    data = requests.get(url=server, params=params).json()
    if len(data['features']) == 0:
        return False
    return True


def create_list_of_products(products: str):
    if '|' in products:
        prods = products.split('|')
        return prods
    return [products]


def count_stars(product):
    raiting = []
    if int(product.raiting) != product.raiting:
        for i in range(int(product.raiting)):
            raiting.append('star')
        raiting.append('star-half')
        if 5 - int(product.raiting) > 1:
            for i in range(5 - int(product.raiting) - 1):
                raiting.append('star-outline')
    else:
        for i in range(int(product.raiting)):
            raiting.append('star')
        if 5 - int(product.raiting) > 0:
            for i in range(5 - int(product.raiting)):
                raiting.append('star-outline')
    return raiting


def adjust_raiting(prod_id, mark, db_sess):
    product = db_sess.query(Product).filter(Product.id == prod_id).first()
    if mark == 1:
        product.one_star += 1
    elif mark == 2:
        product.two_stars += 1
    elif mark == 3:
        product.three_stars += 1
    elif mark == 4:
        product.four_stars += 1
    elif mark == 5:
        product.five_stars += 1

    all_marks = product.one_star + product.two_stars + product.three_stars + product.four_stars + product.five_stars
    pre_raiting = product.one_star + (product.two_stars * 2) + (product.three_stars * 3) + \
                  (product.four_stars * 4) + (product.five_stars * 5)
    product.raiting = pre_raiting / all_marks
    db_sess.commit()


sys.modules['inspect'] = None

if __name__ == '__main__':
    main()
