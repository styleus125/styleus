import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

from models import db, Cart, CartItem, Product, Order, OrderItem
from telegram import send_telegram

checkout_bp = Blueprint('checkout', __name__)


class CheckoutForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    address = TextAreaField('Shipping Address', validators=[Length(max=500)])
    city = StringField('City', validators=[Length(max=100)])
    state = StringField('State / Province', validators=[Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Length(max=20)])
    country = StringField('Country', validators=[Length(max=100)])
    submit = SubmitField('Place Order')


def get_cart_items_and_total():
    items = []
    total = 0
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            for ci in cart.items:
                if ci.product and ci.product.is_active:
                    subtotal = ci.product.price * ci.quantity
                    items.append({'product': ci.product, 'quantity': ci.quantity, 'subtotal': subtotal})
                    total += subtotal
    else:
        sc = session.get('cart', {})
        for pid_str, qty in sc.items():
            product = Product.query.get(int(pid_str))
            if product and product.is_active:
                subtotal = product.price * qty
                items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
                total += subtotal
    return items, total


# CHECKOUT DISABLED — remove the two lines below to re-enable
CHECKOUT_DISABLED = True
CHECKOUT_DISABLED_MSG = 'Checkout is temporarily unavailable. Please check back soon.'


@checkout_bp.route('/', methods=['GET', 'POST'])
def checkout():
    if CHECKOUT_DISABLED:
        flash(CHECKOUT_DISABLED_MSG, 'warning')
        return redirect(url_for('cart.view_cart'))

    items, total = get_cart_items_and_total()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    form = CheckoutForm()
    if current_user.is_authenticated:
        if request.method == 'GET':
            form.email.data = current_user.email
            form.full_name.data = current_user.name

    has_physical = any(i['product'].product_type == 'physical' for i in items)

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    if form.validate_on_submit():
        # Build shipping address
        if has_physical:
            shipping = (
                f"{form.full_name.data}\n"
                f"{form.address.data}\n"
                f"{form.city.data}, {form.state.data} {form.postal_code.data}\n"
                f"{form.country.data}"
            )
        else:
            shipping = ''

        # Create Stripe Payment Intent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),
                currency='inr',
                metadata={'email': form.email.data},
            )
            payment_intent_id = intent.id
        except stripe.error.AuthenticationError:
            # Placeholder keys - simulate payment for demo
            payment_intent_id = 'pi_demo_' + str(int(total * 100))
        except Exception:
            payment_intent_id = 'pi_demo_' + str(int(total * 100))

        # Create order
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            total=total,
            status='processing',
            payment_intent_id=payment_intent_id,
            shipping_address=shipping,
            customer_email=form.email.data,
        )
        db.session.add(order)
        db.session.flush()

        for item_data in items:
            oi = OrderItem(
                order_id=order.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                price_at_purchase=item_data['product'].price,
                product_name=item_data['product'].name,
            )
            db.session.add(oi)
            # Decrease stock for physical
            if item_data['product'].product_type == 'physical':
                item_data['product'].stock = max(0, item_data['product'].stock - item_data['quantity'])

        # Clear cart
        if current_user.is_authenticated:
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if cart:
                CartItem.query.filter_by(cart_id=cart.id).delete()
        else:
            session.pop('cart', None)

        db.session.commit()

        items_summary = ', '.join(
            f"{i['product'].name} x{i['quantity']}" for i in items
        )
        send_telegram(
            f"🛒 <b>New Order #{order.id}</b>\n"
            f"Customer: {order.customer_email}\n"
            f"Total: ₹{order.total:,.2f}\n"
            f"Items: {items_summary}"
        )

        # Store order id in session for success page
        session['last_order_id'] = order.id
        return redirect(url_for('checkout.success'))

    return render_template('checkout/checkout.html',
                           form=form,
                           items=items,
                           total=total,
                           has_physical=has_physical,
                           stripe_public_key=current_app.config['STRIPE_PUBLIC_KEY'],
                           title='Checkout')


@checkout_bp.route('/success')
def success():
    order_id = session.get('last_order_id')
    order = None
    if order_id:
        order = Order.query.get(order_id)
    return render_template('checkout/success.html', order=order, title='Order Confirmed')
