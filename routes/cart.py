from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import current_user
from models import db, Cart, CartItem, Product

cart_bp = Blueprint('cart', __name__)


def get_or_create_db_cart(user):
    cart = Cart.query.filter_by(user_id=user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


def get_session_cart():
    return session.get('cart', {})


def save_session_cart(cart_dict):
    session['cart'] = cart_dict
    session.modified = True


@cart_bp.route('/')
def view_cart():
    if current_user.is_authenticated:
        cart = get_or_create_db_cart(current_user)
        items = []
        for item in cart.items:
            if item.product and item.product.is_active:
                items.append({
                    'id': item.id,
                    'product': item.product,
                    'quantity': item.quantity,
                    'subtotal': item.product.price * item.quantity,
                })
        total = sum(i['subtotal'] for i in items)
    else:
        session_cart = get_session_cart()
        items = []
        total = 0
        for pid_str, qty in session_cart.items():
            product = Product.query.get(int(pid_str))
            if product and product.is_active:
                subtotal = product.price * qty
                items.append({
                    'id': None,
                    'product': product,
                    'quantity': qty,
                    'subtotal': subtotal,
                })
                total += subtotal

    return render_template('cart/cart.html', items=items, total=total, title='Your Cart')


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    if product.product_type == 'physical' and product.stock < quantity:
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

    if current_user.is_authenticated:
        cart = get_or_create_db_cart(current_user)
        existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if existing:
            existing.quantity += quantity
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(item)
        db.session.commit()
        count = cart.get_item_count()
    else:
        cart_dict = get_session_cart()
        pid_str = str(product_id)
        cart_dict[pid_str] = cart_dict.get(pid_str, 0) + quantity
        save_session_cart(cart_dict)
        count = sum(cart_dict.values())

    return jsonify({'success': True, 'message': f'{product.name} added to cart', 'cart_count': count})


@cart_bp.route('/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    product_id = int(data.get('product_id'))
    quantity = int(data.get('quantity', 1))

    if quantity < 1:
        quantity = 1

    if current_user.is_authenticated:
        cart = get_or_create_db_cart(current_user)
        item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if item:
            item.quantity = quantity
            db.session.commit()
        count = cart.get_item_count()
        total = cart.get_total()
        subtotal = item.product.price * quantity if item else 0
    else:
        cart_dict = get_session_cart()
        pid_str = str(product_id)
        if pid_str in cart_dict:
            cart_dict[pid_str] = quantity
            save_session_cart(cart_dict)
        count = sum(cart_dict.values())
        total = sum(Product.query.get(int(k)).price * v for k, v in cart_dict.items()
                    if Product.query.get(int(k)))
        product = Product.query.get(product_id)
        subtotal = product.price * quantity if product else 0

    return jsonify({'success': True, 'cart_count': count, 'total': f'{total:.2f}', 'subtotal': f'{subtotal:.2f}'})


@cart_bp.route('/remove', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = int(data.get('product_id'))

    if current_user.is_authenticated:
        cart = get_or_create_db_cart(current_user)
        item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
        count = cart.get_item_count()
        total = cart.get_total()
    else:
        cart_dict = get_session_cart()
        cart_dict.pop(str(product_id), None)
        save_session_cart(cart_dict)
        count = sum(cart_dict.values())
        total = sum(Product.query.get(int(k)).price * v for k, v in cart_dict.items()
                    if Product.query.get(int(k)))

    return jsonify({'success': True, 'cart_count': count, 'total': f'{total:.2f}'})


@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    if current_user.is_authenticated:
        cart = get_or_create_db_cart(current_user)
        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()
    else:
        save_session_cart({})
    return jsonify({'success': True})
