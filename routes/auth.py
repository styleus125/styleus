from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp, Optional

from models import db, User, PasswordResetRequest
from telegram import send_telegram

auth_bp = Blueprint('auth', __name__)


def _normalize_phone(phone):
    """Return phone in +91XXXXXXXXXX format (last 10 digits with +91 prefix)."""
    import re
    digits = re.sub(r'\D', '', phone)
    ten = digits[-10:] if len(digits) >= 10 else digits
    return f'+91{ten}' if len(ten) == 10 else ten


def _phone_digits(phone):
    """Extract just the last 10 digits for comparison."""
    import re
    digits = re.sub(r'\D', '', phone)
    return digits[-10:] if len(digits) >= 10 else digits


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    name  = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=7, max=20),
        Regexp(r'^[\d\+\-\s\(\)]+$', message='Enter a valid phone number.')
    ])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm  = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    social_handle = StringField('Instagram / Facebook / Other ID', validators=[Optional(), Length(max=200)])
    submit   = SubmitField('Create Account')

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
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            if not user.is_approved:
                flash('Your account is pending admin approval. You will be able to log in once approved.', 'warning')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember.data)
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
        user = User(name=form.name.data, email=form.email.data.lower(), phone=_normalize_phone(form.phone.data),
                    social_handle=form.social_handle.data.strip() if form.social_handle.data else '',
                    is_approved=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_telegram(
            f"👤 <b>New Registration</b>\n"
            f"Name: {user.name}\n"
            f"Email: {user.email}\n"
            f"Phone: {user.phone}\n"
            f"⏳ Pending admin approval"
        )
        flash('Account created! Your account is pending admin approval. You will be notified once approved.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, title='Create Account')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    errors = {}
    form_data = {}
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        raw_phone = request.form.get('phone', '').strip()
        phone = _normalize_phone(raw_phone)
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        form_data = {'email': email, 'phone': raw_phone}

        user = User.query.filter_by(email=email).first()
        if not email:
            errors['email'] = 'Email is required.'
        elif not user:
            errors['email'] = 'No account found with this email.'

        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif user and _phone_digits(user.phone) != _phone_digits(request.form.get('phone', '')):
            errors['phone'] = 'Phone number does not match our records.'

        if not new_password:
            errors['new_password'] = 'New password is required.'
        elif len(new_password) < 6:
            errors['new_password'] = 'Password must be at least 6 characters.'

        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your new password.'
        elif new_password and new_password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if not errors:
            from werkzeug.security import generate_password_hash
            req = PasswordResetRequest(
                user_id=user.id,
                new_password_hash=generate_password_hash(new_password),
                status='pending'
            )
            db.session.add(req)
            db.session.commit()
            send_telegram(
                f"🔑 <b>Password Reset Request</b>\n"
                f"Name: {user.name}\n"
                f"Email: {user.email}\n"
                f"Phone: {user.phone}\n"
                f"⏳ Awaiting admin approval at /admin/password-resets"
            )
            flash('Your password reset request has been submitted. Your current password remains active until an admin approves the change.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', errors=errors, form_data=form_data, title='Forgot Password')


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
