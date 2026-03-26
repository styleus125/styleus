from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models import Order

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders/history.html', orders=orders, title='Order History')


@orders_bp.route('/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('orders/detail.html', order=order, title=f'Order #{order.id}')
