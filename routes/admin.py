import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from werkzeug.utils import secure_filename
from slugify import slugify

from models import db, User, Category, Product, Order, UserListing

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[NumberRange(min=0)], default=0)
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    product_type = SelectField('Type', choices=[('physical', 'Physical'), ('digital', 'Digital')])
    digital_file_url = StringField('Digital File URL', validators=[Optional(), Length(max=300)])
    is_active = BooleanField('Active')
    is_featured = BooleanField('Featured')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only')])
    submit = SubmitField('Save Product')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_product_image(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        import time
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{int(time.time())}{ext}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        return f'/static/uploads/{unique_filename}'
    return None


# ── Dashboard ──────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_products = Product.query.filter_by(is_active=True).count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.status != 'cancelled'
    ).scalar() or 0

    today = datetime.utcnow().date()
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    pending_listings = UserListing.query.filter_by(status='pending').count()
    pending_users = User.query.filter_by(is_approved=False).count()

    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_users=total_users,
                           total_revenue=total_revenue,
                           orders_today=orders_today,
                           recent_orders=recent_orders,
                           pending_listings=pending_listings,
                           pending_users=pending_users,
                           title='Admin Dashboard')


# ── Products ──────────────────────────────────────────────────────────────────

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False)
    return render_template('admin/products.html',
                           products=pagination.items,
                           pagination=pagination,
                           search=search,
                           title='Manage Products')


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def product_new():
    form = ProductForm(is_active=True)
    form.category_id.choices = [(0, '-- None --')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    if form.validate_on_submit():
        image_url = save_product_image(request.files.get('image')) or ''
        slug = slugify(form.name.data)
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        product = Product(
            name=form.name.data,
            slug=slug,
            description=form.description.data or '',
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data if form.category_id.data else None,
            product_type=form.product_type.data,
            digital_file_url=form.digital_file_url.data or '',
            is_active=form.is_active.data,
            is_featured=form.is_featured.data,
            image_url=image_url,
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" created.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', form=form, product=None, title='New Product')


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(0, '-- None --')] + [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    if form.validate_on_submit():
        new_image = save_product_image(request.files.get('image'))
        if new_image:
            product.image_url = new_image
        product.name = form.name.data
        product.description = form.description.data or ''
        product.price = form.price.data
        product.stock = form.stock.data
        product.category_id = form.category_id.data if form.category_id.data else None
        product.product_type = form.product_type.data
        product.digital_file_url = form.digital_file_url.data or ''
        product.is_active = form.is_active.data
        product.is_featured = form.is_featured.data
        db.session.commit()
        flash(f'Product "{product.name}" updated.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted.', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@login_required
@admin_required
def product_toggle(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    status = 'activated' if product.is_active else 'deactivated'
    flash(f'Product "{product.name}" {status}.', 'info')
    return redirect(url_for('admin.products'))


# ── Orders ────────────────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False)
    return render_template('admin/orders.html',
                           orders=pagination.items,
                           pagination=pagination,
                           status_filter=status_filter,
                           status_choices=Order.STATUS_CHOICES,
                           title='Manage Orders')


@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order, title=f'Order #{order.id}')


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in Order.STATUS_CHOICES:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.orders'))


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('filter', '')
    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ADMIN_ITEMS_PER_PAGE'], error_out=False)
    return render_template('admin/users.html',
                           users=pagination.items,
                           pagination=pagination,
                           search=search,
                           title='Manage Users')


@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@login_required
@admin_required
def user_approve(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.email} approved.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def user_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = 'granted admin' if user.is_admin else 'revoked admin'
        flash(f'User {user.email} {status}.', 'info')
    return redirect(url_for('admin.users'))


# ── Categories ────────────────────────────────────────────────────────────────

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    form = CategoryForm()
    return render_template('admin/categories.html', categories=cats, form=form, title='Manage Categories')


@admin_bp.route('/categories/new', methods=['POST'])
@login_required
@admin_required
def category_new():
    form = CategoryForm()
    if form.validate_on_submit():
        slug = slugify(form.name.data)
        base_slug = slug
        counter = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1
        cat = Category(name=form.name.data, slug=slug, description=form.description.data or '')
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" created.', 'success')
    else:
        flash('Invalid form data.', 'danger')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/edit', methods=['POST'])
@login_required
@admin_required
def category_edit(cat_id):
    cat = Category.query.get_or_404(cat_id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if name:
        cat.name = name
        cat.description = description
        db.session.commit()
        flash(f'Category "{cat.name}" updated.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@admin_required
def category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    name = cat.name
    # Unlink products
    Product.query.filter_by(category_id=cat.id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{name}" deleted.', 'success')
    return redirect(url_for('admin.categories'))


# ── User Listings ─────────────────────────────────────────────────────────────

@admin_bp.route('/listings')
@login_required
@admin_required
def listings():
    status_filter = request.args.get('status', 'pending')
    query = UserListing.query
    if status_filter in ('pending', 'approved', 'rejected'):
        query = query.filter_by(status=status_filter)
    items = query.order_by(UserListing.created_at.desc()).all()
    pending_count = UserListing.query.filter_by(status='pending').count()
    return render_template('admin/listings.html',
                           listings=items,
                           status_filter=status_filter,
                           pending_count=pending_count,
                           title='User Listings')


@admin_bp.route('/listings/<int:listing_id>/approve', methods=['POST'])
@login_required
@admin_required
def listing_approve(listing_id):
    listing = UserListing.query.get_or_404(listing_id)
    listing.status = 'approved'
    listing.admin_note = request.form.get('note', '')
    db.session.commit()
    flash(f'Listing "{listing.title}" approved.', 'success')
    return redirect(url_for('admin.listings'))


@admin_bp.route('/listings/<int:listing_id>/reject', methods=['POST'])
@login_required
@admin_required
def listing_reject(listing_id):
    listing = UserListing.query.get_or_404(listing_id)
    listing.status = 'rejected'
    listing.admin_note = request.form.get('note', '')
    db.session.commit()
    flash(f'Listing "{listing.title}" rejected.', 'info')
    return redirect(url_for('admin.listings'))
