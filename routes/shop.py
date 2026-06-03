import re
import random
from datetime import date

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response, session
from flask_login import current_user, login_required
from sqlalchemy import func
from models import db, Product, Category, ProductLike, UserListing, Service, Review, Enquiry, Professional, BlogPost, CustomerReview
from telegram import send_telegram

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def index():
    featured = Product.query.filter_by(is_active=True, is_featured=True).order_by(func.random()).limit(10).all()
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


@shop_bp.route('/webhosting')
def webhosting():
    return render_template('webhosting.html', title='Web Hosting & Maintenance')


@shop_bp.route('/software-development')
def software_development():
    return render_template('software_development.html', title='Software Development')


@shop_bp.route('/review', methods=['GET', 'POST'])
def review_form():
    errors = {}
    form_data = {}
    submitted = False

    if request.method == 'GET':
        a, b = random.randint(1, 9), random.randint(1, 9)
        session['captcha_answer'] = a + b
        session['captcha_q'] = f'{a} + {b}'

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        stars = request.form.get('stars', type=int)
        comment = request.form.get('comment', '').strip()
        captcha_input = request.form.get('captcha', '').strip()

        form_data = {'name': name, 'email': email, 'phone': phone, 'stars': stars, 'comment': comment}

        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif not _EMAIL_RE.match(email):
            errors['email'] = 'Enter a valid email address.'
        if not stars or not (1 <= stars <= 5):
            errors['stars'] = 'Please select a star rating.'
        if not comment or len(comment) < 10:
            errors['comment'] = f'Comment must be at least 10 characters (currently {len(comment)}).'

        try:
            captcha_val = int(captcha_input)
        except (ValueError, TypeError):
            captcha_val = None
        if captcha_val != session.get('captcha_answer'):
            errors['captcha'] = 'Incorrect answer — please try again.'

        if not errors:
            db.session.add(CustomerReview(
                name=name, email=email,
                phone=phone if phone else None,
                stars=stars, comment=comment
            ))
            db.session.commit()
            session.pop('captcha_answer', None)
            session.pop('captcha_q', None)
            submitted = True
        else:
            a, b = random.randint(1, 9), random.randint(1, 9)
            session['captcha_answer'] = a + b
            session['captcha_q'] = f'{a} + {b}'

    captcha_q = session.get('captcha_q', '? + ?')
    return render_template('review_form.html',
                           errors=errors,
                           form_data=form_data,
                           submitted=submitted,
                           captcha_q=captcha_q,
                           title='Leave a Review')


@shop_bp.route('/sitemap.xml')
def sitemap():
    today = date.today().isoformat()
    base = request.host_url.rstrip('/')

    static_urls = [
        ('/', 'daily', '1.0'),
        ('/products', 'daily', '0.9'),
        ('/blog', 'daily', '0.9'),
        ('/services', 'weekly', '0.8'),
        ('/webhosting', 'weekly', '0.8'),
        ('/software-development', 'weekly', '0.8'),
        ('/professionals', 'weekly', '0.7'),
        ('/sell/listings', 'daily', '0.7'),
        ('/sell', 'weekly', '0.6'),
        ('/about', 'monthly', '0.6'),
        ('/privacy', 'monthly', '0.5'),
        ('/enquiry', 'monthly', '0.6'),
        ('/search', 'monthly', '0.5'),
        ('/auth/login', 'monthly', '0.3'),
        ('/auth/register', 'monthly', '0.3'),
    ]

    products   = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()
    blog_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).all()

    urls = []
    for path, freq, priority in static_urls:
        urls.append(f"""  <url>
    <loc>{base}{path}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    for product in products:
        urls.append(f"""  <url>
    <loc>{base}/products/{product.slug}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

    for cat in categories:
        urls.append(f"""  <url>
    <loc>{base}/products?category={cat.slug}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>""")

    for post in blog_posts:
        post_date = post.created_at.date().isoformat() if post.created_at else today
        urls.append(f"""  <url>
    <loc>{base}/blog/{post.slug}</loc>
    <lastmod>{post_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls)
    xml += '\n</urlset>'

    return Response(xml, mimetype='application/xml')


@shop_bp.route('/robots.txt')
def robots():
    base = request.host_url.rstrip('/')
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /cart/
Disallow: /orders
Disallow: /auth/

Sitemap: {base}/sitemap.xml
"""
    return Response(content, mimetype='text/plain')


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
            send_telegram(
                f"🔧 <b>New Tech Enquiry</b>\n"
                f"Email: {email}\n"
                f"Phone: {phone}\n"
                f"Details: {details[:300]}"
            )
            flash('Your query has been submitted. You will receive a response within 24 hours.', 'success')
            return redirect(url_for('shop.enquiry'))

    return render_template('enquiry.html', errors=errors, form_data=form_data, title='Tech Enquiries')


@shop_bp.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    pagination = (BlogPost.query
                  .filter_by(is_published=True)
                  .order_by(BlogPost.created_at.desc())
                  .paginate(page=page, per_page=9, error_out=False))
    return render_template('blog/list.html', posts=pagination.items, pagination=pagination, title='Blog')


@shop_bp.route('/blog/<slug>')
def blog_post(slug):
    import mistune
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    body_html = mistune.html(post.body)
    return render_template('blog/post.html', post=post, body_html=body_html, title=post.title)


@shop_bp.route('/about')
def about():
    return render_template('about.html', title='About Us')


@shop_bp.route('/privacy')
def privacy():
    return render_template('privacy.html', title='Privacy Policy')


@shop_bp.route('/professionals')
def professionals():
    items = Professional.query.filter_by(status='approved').order_by(Professional.created_at.desc()).all()
    return render_template('professionals.html', professionals=items, title='Professionals')


@shop_bp.route('/professionals/register', methods=['GET', 'POST'])
@login_required
def professional_register():
    existing = Professional.query.filter_by(user_id=current_user.id).first()
    errors = {}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        profession = request.form.get('profession', '').strip()
        if not name:
            errors['name'] = 'Name / Company is required.'
        if not address:
            errors['address'] = 'Address is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif not re.fullmatch(r'[6-9]\d{9}', phone.replace(' ', '').replace('-', '')):
            errors['phone'] = 'Enter a valid 10-digit Indian mobile number (starting with 6–9).'
        if not profession:
            errors['profession'] = 'Area of Work / Profession is required.'
        elif len(profession) < 100:
            errors['profession'] = f'Please describe in at least 100 characters ({len(profession)}/100).'
        if not errors:
            if existing:
                existing.name = name
                existing.address = address
                existing.phone = phone
                existing.profession = profession
                existing.status = 'pending'
                action = 'updated'
            else:
                db.session.add(Professional(user_id=current_user.id, name=name, address=address, phone=phone, profession=profession))
                action = 'registered'
            db.session.commit()
            send_telegram(
                f"👷 <b>Professional {action.title()}</b>\n"
                f"Name: {name}\n"
                f"Phone: +91{phone}\n"
                f"Address: {address[:100]}\n"
                f"Profession: {profession[:200]}"
            )
            flash('Your professional details have been submitted for approval.', 'success')
            return redirect(url_for('shop.professionals'))
        return render_template('professional_register.html', errors=errors, existing=existing, title='Register as Professional')
    return render_template('professional_register.html', errors=errors, existing=existing, title='Register as Professional')


def _multi_search(fields, q):
    """Match full phrase OR every individual word across the given fields."""
    phrase = db.or_(*[f.ilike(f'%{q}%') for f in fields])
    words = [w for w in q.split() if len(w) >= 2]
    if len(words) < 2:
        return phrase
    word_clauses = [db.or_(*[f.ilike(f'%{w}%') for f in fields]) for w in words]
    return db.or_(phrase, db.and_(*word_clauses))


@shop_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    shop_results = []
    used_results = []
    service_results = []
    professional_results = []
    if q:
        shop_results = Product.query.filter(
            Product.is_active.is_(True),
            _multi_search([Product.name, Product.description], q)
        ).order_by(Product.created_at.desc()).limit(40).all()
        used_results = UserListing.query.filter(
            UserListing.status == 'approved',
            UserListing.is_active.is_(True),
            _multi_search([UserListing.title, UserListing.description], q)
        ).order_by(UserListing.created_at.desc()).limit(40).all()
        service_results = Service.query.filter(
            Service.is_active.is_(True),
            _multi_search([Service.name, Service.description], q)
        ).order_by(Service.sort_order, Service.name).all()
        professional_results = Professional.query.filter(
            Professional.status == 'approved',
            _multi_search([Professional.name, Professional.profession, Professional.address], q)
        ).order_by(Professional.created_at.desc()).limit(20).all()
    return render_template('shop/search_results.html',
                           q=q,
                           shop_results=shop_results,
                           used_results=used_results,
                           service_results=service_results,
                           professional_results=professional_results,
                           title=f'Search: {q}' if q else 'Search')
