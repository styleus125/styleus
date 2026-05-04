from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, default='')
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    social_handle = db.Column(db.String(200), nullable=False, default='', server_default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cart = db.relationship('Cart', backref='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, default='')

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    product_type = db.Column(db.String(20), default='physical')  # physical / digital
    image_url = db.Column(db.String(300), default='')
    image_url_2 = db.Column(db.String(300), default='')
    image_url_3 = db.Column(db.String(300), default='')
    image_url_4 = db.Column(db.String(300), default='')
    digital_file_url = db.Column(db.String(300), default='')
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    @property
    def all_images(self):
        return [u for u in [self.image_url, self.image_url_2, self.image_url_3, self.image_url_4] if u]

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def avg_rating(self):
        from sqlalchemy import func
        result = db.session.query(func.avg(Review.rating)).filter_by(product_id=self.id).scalar()
        return round(float(result), 1) if result else None

    def __repr__(self):
        return f'<Product {self.name}>'


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart', cascade='all, delete-orphan', lazy='dynamic')

    def get_total(self):
        return sum(item.product.price * item.quantity for item in self.items if item.product)

    def get_item_count(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f'<Cart user_id={self.user_id}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    def __repr__(self):
        return f'<CartItem product_id={self.product_id} qty={self.quantity}>'


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='pending')  # pending/processing/shipped/delivered/cancelled
    payment_intent_id = db.Column(db.String(200), default='')
    shipping_address = db.Column(db.Text, default='')
    customer_email = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy='dynamic')

    STATUS_CHOICES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

    def __repr__(self):
        return f'<Order #{self.id} {self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    product_name = db.Column(db.String(200), default='')

    def __repr__(self):
        return f'<OrderItem order_id={self.order_id} product={self.product_name}>'


class SellCategory(db.Model):
    __tablename__ = 'sell_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    listings = db.relationship('UserListing', backref='sell_category', lazy='dynamic')

    def __repr__(self):
        return f'<SellCategory {self.name}>'


class UserListing(db.Model):
    __tablename__ = 'user_listings'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sell_category_id = db.Column(db.Integer, db.ForeignKey('sell_categories.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    asking_price = db.Column(db.Float, nullable=True)
    condition = db.Column(db.String(50), default='good')
    image_url = db.Column(db.String(300), default='')
    image_url_2 = db.Column(db.String(300), default='')
    image_url_3 = db.Column(db.String(300), default='')
    image_url_4 = db.Column(db.String(300), default='')
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    admin_note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seller = db.relationship('User', backref=db.backref('listings', lazy='dynamic'))

    CONDITION_CHOICES = [('like_new', 'Like New'), ('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor')]

    @property
    def all_images(self):
        return [u for u in [self.image_url, self.image_url_2, self.image_url_3, self.image_url_4] if u]

    def __repr__(self):
        return f'<UserListing #{self.id} {self.title}>'


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.name}>'


class Enquiry(db.Model):
    __tablename__ = 'enquiries'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Enquiry {self.email}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1–5
    body = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('reviews', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('reviews', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_review_user_product'),)

    def __repr__(self):
        return f'<Review product={self.product_id} user={self.user_id} rating={self.rating}>'


class ProductLike(db.Model):
    __tablename__ = 'product_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)

    def __repr__(self):
        return f'<ProductLike user={self.user_id} product={self.product_id}>'
