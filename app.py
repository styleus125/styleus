import os
import click
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User, Category, Product

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from routes.auth import auth_bp
    from routes.shop import shop_bp
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp
    from routes.sell import sell_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(checkout_bp, url_prefix='/checkout')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sell_bp, url_prefix='/')

    # Context processor for cart count + date
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    @app.context_processor
    def inject_liked_ids():
        from flask_login import current_user
        from models import ProductLike
        liked_ids = set()
        if current_user.is_authenticated:
            liked_ids = {lk.product_id for lk in ProductLike.query.filter_by(user_id=current_user.id).all()}
        return {'liked_ids': liked_ids}

    @app.context_processor
    def inject_cart_count():
        from flask_login import current_user
        from models import Cart
        count = 0
        if current_user.is_authenticated:
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if cart:
                count = cart.get_item_count()
        else:
            session_cart = session.get('cart', {})
            count = sum(session_cart.values())
        return {'cart_count': count}

    # Seed CLI command
    @app.cli.command('seed')
    def seed_db():
        """Seed the database with sample data."""
        db.create_all()

        # Create admin user
        if not User.query.filter_by(email='admin@dlo.com').first():
            admin = User(name='Admin', email='admin@dlo.com', is_admin=True, is_approved=True)
            admin.set_password('admin123')
            db.session.add(admin)
            click.echo('Created admin user: admin@dlo.com / admin123')

        # Create categories
        categories_data = [
            ('Electronics', 'electronics', 'Gadgets, devices and tech accessories'),
            ('Clothing', 'clothing', 'Apparel, shoes and fashion items'),
            ('Books', 'books', 'Physical and digital books across all genres'),
            ('Software', 'software', 'Digital software licenses and applications'),
            ('Music', 'music', 'Digital music downloads and albums'),
        ]

        categories = {}
        for name, slug, desc in categories_data:
            cat = Category.query.filter_by(slug=slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc)
                db.session.add(cat)
                db.session.flush()
            categories[slug] = cat
        db.session.flush()

        # Sample products
        products_data = [
            # Electronics (physical)
            ('Wireless Noise-Cancelling Headphones', 'electronics', 'physical', 149.99, 50),
            ('4K Ultra HD Smart TV 55"', 'electronics', 'physical', 699.99, 15),
            ('Mechanical Gaming Keyboard RGB', 'electronics', 'physical', 89.99, 75),
            ('Portable Bluetooth Speaker', 'electronics', 'physical', 59.99, 100),
            ('USB-C Hub 7-in-1', 'electronics', 'physical', 39.99, 200),
            ('Wireless Charging Pad', 'electronics', 'physical', 24.99, 150),
            ('Smart Watch Fitness Tracker', 'electronics', 'physical', 129.99, 60),
            ('Laptop Stand Adjustable', 'electronics', 'physical', 34.99, 120),
            ('Webcam 1080p HD', 'electronics', 'physical', 69.99, 80),
            ('Mechanical Mouse Gaming', 'electronics', 'physical', 44.99, 90),
            ('27" IPS Monitor', 'electronics', 'physical', 299.99, 25),
            ('Portable SSD 1TB', 'electronics', 'physical', 99.99, 45),
            ('Noise-Cancelling Earbuds', 'electronics', 'physical', 79.99, 110),
            ('Smart Home Hub', 'electronics', 'physical', 119.99, 35),
            ('Action Camera 4K', 'electronics', 'physical', 189.99, 30),

            # Clothing (physical)
            ('Classic White Oxford Shirt', 'clothing', 'physical', 49.99, 200),
            ('Premium Denim Jeans', 'clothing', 'physical', 79.99, 150),
            ('Running Sneakers Pro', 'clothing', 'physical', 99.99, 80),
            ('Merino Wool Sweater', 'clothing', 'physical', 89.99, 60),
            ('Leather Belt Classic', 'clothing', 'physical', 34.99, 100),
            ('Casual Chino Pants', 'clothing', 'physical', 54.99, 120),
            ('Winter Puffer Jacket', 'clothing', 'physical', 149.99, 40),
            ('Cotton T-Shirt 3-Pack', 'clothing', 'physical', 29.99, 300),
            ('Sports Shorts Quick-Dry', 'clothing', 'physical', 24.99, 200),
            ('Canvas Backpack 25L', 'clothing', 'physical', 59.99, 75),

            # Books (physical + digital mix)
            ('The Art of Programming', 'books', 'physical', 39.99, 60),
            ('Clean Code: A Handbook', 'books', 'digital', 19.99, 999),
            ('Design Patterns Explained', 'books', 'physical', 44.99, 45),
            ('Python for Data Science', 'books', 'digital', 24.99, 999),
            ('The Pragmatic Programmer', 'books', 'digital', 29.99, 999),
            ('JavaScript: The Good Parts', 'books', 'digital', 14.99, 999),
            ('Deep Learning Fundamentals', 'books', 'physical', 54.99, 30),
            ('System Design Interview', 'books', 'digital', 34.99, 999),
            ('The Lean Startup', 'books', 'physical', 22.99, 80),
            ('Atomic Habits', 'books', 'digital', 12.99, 999),

            # Software (digital)
            ('Pro Photo Editor Suite', 'software', 'digital', 79.99, 999),
            ('Video Editor Professional', 'software', 'digital', 129.99, 999),
            ('VPN Service 1-Year License', 'software', 'digital', 49.99, 999),
            ('Password Manager Premium', 'software', 'digital', 29.99, 999),
            ('Antivirus Suite 3 Devices', 'software', 'digital', 39.99, 999),
            ('Office Suite Pro License', 'software', 'digital', 99.99, 999),
            ('Cloud Storage 2TB Annual', 'software', 'digital', 59.99, 999),
            ('Project Management Tool', 'software', 'digital', 89.99, 999),
            ('Code Editor Pro License', 'software', 'digital', 69.99, 999),
            ('Design Tool Professional', 'software', 'digital', 119.99, 999),

            # Music (digital)
            ('Chill Lo-Fi Beats Vol. 1', 'music', 'digital', 9.99, 999),
            ('Electronic Dance Anthology', 'music', 'digital', 14.99, 999),
            ('Jazz Collection Classics', 'music', 'digital', 12.99, 999),
            ('Acoustic Sessions Vol. 3', 'music', 'digital', 9.99, 999),
            ('Hip-Hop Instrumentals Pack', 'music', 'digital', 19.99, 999),
            ('Classical Piano Collection', 'music', 'digital', 12.99, 999),
            ('Rock Anthems Ultimate Mix', 'music', 'digital', 14.99, 999),
            ('Nature Sounds & Ambience', 'music', 'digital', 7.99, 999),
            ('Meditation & Mindfulness Tracks', 'music', 'digital', 9.99, 999),
            ('Film Score Essentials', 'music', 'digital', 17.99, 999),
        ]

        from slugify import slugify
        featured_indices = [0, 1, 6, 10, 16, 26, 35, 45]

        for i, (name, cat_slug, ptype, price, stock) in enumerate(products_data):
            slug = slugify(name)
            if Product.query.filter_by(slug=slug).first():
                continue
            product = Product(
                name=name,
                slug=slug,
                description=(
                    f'High quality {name.lower()}. {categories[cat_slug].description}. '
                    'Perfect for everyday use.'
                ),
                price=price,
                stock=stock,
                category_id=categories[cat_slug].id,
                product_type=ptype,
                is_active=True,
                is_featured=(i in featured_indices),
                digital_file_url='/static/downloads/sample.zip' if ptype == 'digital' else '',
            )
            db.session.add(product)

        db.session.commit()
        click.echo(f'Seeded {len(products_data)} products across 5 categories.')
        click.echo('Done!')

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
