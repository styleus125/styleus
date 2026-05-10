import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "dlo.db")}'
    )

    # Ensure data directory exists (used in Docker)
    @staticmethod
    def init_app(app):
        data_dir = '/app/data'
        if os.path.exists('/app'):
            os.makedirs(data_dir, exist_ok=True)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Stripe keys (replace with real keys in production)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_placeholder_key_replace_with_real')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder_key_replace_with_real')

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB hard ceiling (4 × 2 MB + overhead)
    MAX_IMAGE_SIZE     =  2 * 1024 * 1024   # 2 MB per individual photo
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Telegram notifications
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # Pagination
    PRODUCTS_PER_PAGE = 20
    ADMIN_ITEMS_PER_PAGE = 25
