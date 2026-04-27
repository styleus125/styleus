from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from models import db, Product, Category, ProductLike, UserListing

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def index():
    featured = Product.query.filter_by(is_active=True, is_featured=True).limit(8).all()
    categories = Category.query.all()
    new_arrivals = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template('index.html',
                           featured=featured,
                           categories=categories,
                           new_arrivals=new_arrivals,
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
    return render_template('shop/product.html',
                           product=product,
                           related=related,
                           title=product.name)


@shop_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    shop_results = []
    used_results = []
    if q:
        shop_results = Product.query.filter(
            Product.is_active.is_(True),
            Product.name.ilike(f'%{q}%')
        ).order_by(Product.created_at.desc()).limit(40).all()
        used_results = UserListing.query.filter(
            UserListing.status == 'approved',
            UserListing.title.ilike(f'%{q}%')
        ).order_by(UserListing.created_at.desc()).limit(40).all()
    return render_template('shop/search_results.html',
                           q=q,
                           shop_results=shop_results,
                           used_results=used_results,
                           title=f'Search: {q}' if q else 'Search')
