from flask import render_template, redirect, url_for, flash, request, session
from types import SimpleNamespace
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

from .models.user import User
from .models.purchase import Purchase
from .models.buyer_order import BuyerOrder
from .models.inventory import InventoryItem
from .models.feedback import Feedback


from flask import Blueprint
bp = Blueprint('users', __name__)


def email_or_local(form, field):
    # Implemented as a fix to the incompatability with earlier email handling and the 
    # .local extension for generated emails. Makes it so (for test build), .local is seen as valid
    value = (field.data or '').strip()
    if value.lower().endswith('.local'):
        # Accept seeded local test accounts like user@marketplace.local
        if '@' in value and not value.startswith('@') and not value.endswith('@'):
            return
        raise ValidationError('Invalid email address.')
    Email()(form, field)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), email_or_local])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)

        # Merge guest cart if any
        guest_cart = session.pop('guest_cart', None)
        if guest_cart:
            from .models.cart import CartItem
            CartItem.merge_guest_cart(user.id, guest_cart)
            flash(f'{len(guest_cart)} item(s) from your guest cart have been added.', 'info')

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), email_or_local])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                       EqualTo('password')])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                         form.password.data,
                         form.firstname.data,
                         form.lastname.data,
                         form.address.data):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))


@bp.route('/balance', methods=['GET', 'POST'])
@login_required
def balance():
    if request.method == 'POST':
        amount = request.form.get('amount', '')
        operation = request.form.get('operation', '')
        updated_user, error = User.update_balance(current_user.id, amount, operation)

        if error:
            flash(error)
        else:
            flash(f'Balance updated successfully. Current balance: ${updated_user.balance:.2f}')

        return redirect(url_for('users.balance'))

    orders, _ = BuyerOrder.get_orders_by_user(
        current_user.id,
        page=1,
        per_page=10,
        sort_by='date_desc',
    )

    return render_template('balance.html', recent_orders=orders)


@bp.route('/users/public')
def public_profile():
    user_id = request.args.get('user_id', type=int)
    if user_id is None:
        return render_template('user_public.html', user=None)

    user = User.get(user_id)
    if user is None:
        flash(f'No user found with ID {user_id}.')
        return render_template('user_public.html', user=None)

    storefront = InventoryItem.get_storefront_stats(user_id)
    is_seller = False
    if storefront is not None:
        listing_count = storefront[4]
        active_listing_count = storefront[5]
        review_count_from_storefront = storefront[9]
        is_seller = bool(listing_count or active_listing_count or review_count_from_storefront)

    reviews = []
    avg_rating = None
    review_count = 0
    if is_seller:
        review_count = Feedback.get_seller_review_count(user_id)
        avg_rating = Feedback.get_seller_average_rating(user_id)
        if review_count:
            reviews = Feedback.get_seller_reviews(user_id, page=1, per_page=review_count)

    return render_template(
        'user_public.html',
        user=user,
        is_seller=is_seller,
        storefront=storefront,
        reviews=reviews,
        review_count=review_count,
        avg_rating=avg_rating,
    )


@bp.route('/user_purchases')
def user_purchases():
    user_id = request.args.get('user_id', type=int)
    user = User.get(user_id)
    if user is None:
        #did not find a user
        flash('User not found')
        return redirect(url_for('index.index', user_id=user_id))

    purchases = Purchase.get_all_by_uid_with_product(user_id)
    items = []
    for row in purchases:
        purchase = Purchase(row[0], row[1], row[2], row[3])
        product = None
        if row[4] is not None:
            product = SimpleNamespace(name=row[4], price=float(row[5]) if row[5] is not None else 0.0)
        items.append({'purchase': purchase, 'product': product})

    return render_template('purchases.html', purchases=items, user=user)


