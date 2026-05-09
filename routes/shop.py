import re

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from models import db, Product, Category, ProductLike, UserListing, Service, Review, Enquiry

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def index():
    featured = Product.query.filter_by(is_active=True, is_featured=True).limit(10).all()
    categories = Category.query.all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    highlight_services = (Service.query.filter_by(is_active=True)
                          .order_by(Service.sort_order, Service.name).limit(6).all())
    user_deals = (UserListing.query.filter_by(status='approved', is_active=True)
                  .order_by(UserListing.created_at.desc()).limit(8).all())
    return render_template('index.html',
                           featured=featured,
                           categories=categories,
                           new_arrivals=new_arrivals,
                           highlight_services=highlight_services,
                           user_deals=user_deals,
                           title='Styleus')


@shop_bp.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '')
    product_type = request.args.get('type', '')
    min_price = request.args.get('min_price', '', type=str)
    max_price = request.args.get('max_price', '', type=str)
    sort = request.args.get('sort', 'newest')

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if product_type in ('physical', 'digital'):
        query = query.filter_by(product_type=product_type)

    if min_price:
        try:
            query = query.filter(Product.price >= float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            query = query.filter(Product.price <= float(max_price))
        except ValueError:
            pass

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.all()

    return render_template('shop/products.html',
                           products=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           search=search,
                           category_slug=category_slug,
                           product_type=product_type,
                           min_price=min_price,
                           max_price=max_price,
                           sort=sort,
                           title='Shop')


@shop_bp.route('/products/<int:product_id>/like', methods=['POST'])
def toggle_like(product_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'login_required'}), 401
    Product.query.get_or_404(product_id)
    existing = ProductLike.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(ProductLike(user_id=current_user.id, product_id=product_id))
        liked = True
    db.session.commit()
    count = ProductLike.query.filter_by(product_id=product_id).count()
    return jsonify({'liked': liked, 'count': count})


@shop_bp.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active.is_(True)
    ).limit(4).all()

    reviews = (Review.query.filter_by(product_id=product.id)
               .order_by(Review.created_at.desc()).all())
    avg_rating = (db.session.query(func.avg(Review.rating))
                  .filter_by(product_id=product.id).scalar())
    avg_rating = round(float(avg_rating), 1) if avg_rating else None

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            product_id=product.id, user_id=current_user.id).first()

    liked_ids = []
    if current_user.is_authenticated:
        liked_ids = [
            pl.product_id for pl in
            ProductLike.query.filter_by(user_id=current_user.id).all()
        ]

    return render_template('shop/product.html',
                           product=product,
                           related=related,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           user_review=user_review,
                           liked_ids=liked_ids,
                           title=product.name)


@shop_bp.route('/products/<slug>/review', methods=['POST'])
@login_required
def submit_review(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    rating = request.form.get('rating', type=int)
    body = request.form.get('body', '').strip()

    if not rating or not (1 <= rating <= 5):
        flash('Please select a star rating.', 'warning')
        return redirect(url_for('shop.product_detail', slug=slug))

    existing = Review.query.filter_by(product_id=product.id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
        existing.body = body
        flash('Your review has been updated.', 'success')
    else:
        db.session.add(Review(
            product_id=product.id,
            user_id=current_user.id,
            rating=rating,
            body=body
        ))
        flash('Review submitted — thank you!', 'success')

    db.session.commit()
    return redirect(url_for('shop.product_detail', slug=slug) + '#reviews')


@shop_bp.route('/services')
def services():
    items = Service.query.filter_by(is_active=True).order_by(Service.sort_order, Service.name).all()
    return render_template('services.html', services=items, title='Services')


_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^(\+91|91|0)?[6-9]\d{9}$')


@shop_bp.route('/enquiry', methods=['GET', 'POST'])
def enquiry():
    errors = {}
    form_data = {}
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = re.sub(r'[\s\-\(\)]', '', request.form.get('phone', ''))
        details = request.form.get('details', '').strip()
        form_data = {'email': email, 'phone': request.form.get('phone', ''), 'details': details}

        if not email:
            errors['email'] = 'Email is required.'
        elif not _EMAIL_RE.match(email):
            errors['email'] = 'Enter a valid email address.'

        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif not _PHONE_RE.match(phone):
            errors['phone'] = 'Enter a valid 10-digit Indian mobile number.'

        if not details:
            errors['details'] = 'Details are required.'
        elif len(details) < 25:
            errors['details'] = f'Details must be at least 25 characters (currently {len(details)}).'

        if not errors:
            db.session.add(Enquiry(email=email, phone=phone, details=details))
            db.session.commit()
            flash('Your query has been submitted. You will receive a response within 24 hours.', 'success')
            return redirect(url_for('shop.enquiry'))

    return render_template('enquiry.html', errors=errors, form_data=form_data, title='Tech Enquiries')


@shop_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    shop_results = []
    used_results = []
    service_results = []
    if q:
        shop_results = Product.query.filter(
            Product.is_active.is_(True),
            Product.name.ilike(f'%{q}%')
        ).order_by(Product.created_at.desc()).limit(40).all()
        used_results = UserListing.query.filter(
            UserListing.status == 'approved',
            UserListing.is_active.is_(True),
            UserListing.title.ilike(f'%{q}%')
        ).order_by(UserListing.created_at.desc()).limit(40).all()
        service_results = Service.query.filter(
            Service.is_active.is_(True),
            Service.name.ilike(f'%{q}%')
        ).order_by(Service.sort_order, Service.name).all()
    return render_template('shop/search_results.html',
                           q=q,
                           shop_results=shop_results,
                           used_results=used_results,
                           service_results=service_results,
                           title=f'Search: {q}' if q else 'Search')
