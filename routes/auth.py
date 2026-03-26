from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from models import db, User

auth_bp = Blueprint('auth', __name__)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Merge session cart into DB cart
            _merge_session_cart(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page or url_for('shop.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form, title='Sign In')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        _merge_session_cart(user)
        flash('Account created! Welcome to Delhi Outlook.', 'success')
        return redirect(url_for('shop.index'))
    return render_template('auth/register.html', form=form, title='Create Account')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('shop.index'))


def _merge_session_cart(user):
    """Merge session cart items into user's DB cart on login."""
    from flask import session
    from models import Cart, CartItem, Product
    session_cart = session.get('cart', {})
    if not session_cart:
        return
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.flush()
    for product_id_str, qty in session_cart.items():
        product_id = int(product_id_str)
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            continue
        existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if existing:
            existing.quantity += qty
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=qty)
            db.session.add(item)
    db.session.commit()
    session.pop('cart', None)
