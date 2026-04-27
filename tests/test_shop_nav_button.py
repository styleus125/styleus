"""
Tests for the Shop nav-link restyling change.
The plain text anchor was replaced with a blue pill button
(bg-blue-500 hover:bg-blue-600) matching the +Sell button pattern.
"""
import pytest
from models import db, User


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_html(client, path='/'):
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _navbar_html(client, path='/'):
    html = _get_html(client, path)
    nav_start = html.index('<nav ')
    nav_end = html.index('</nav>') + len('</nav>')
    return html[nav_start:nav_end]


def _shop_anchor(client, path='/'):
    """Return the full opening <a> tag for the Shop nav link."""
    nav = _navbar_html(client, path)
    # Find the Shop text inside the navbar and back-trace to its <a>
    shop_pos = nav.index('>Shop<')
    a_start = nav.rindex('<a ', 0, shop_pos)
    a_end = nav.index('>', a_start) + 1
    return nav[a_start:a_end]


@pytest.fixture
def approved_user(app):
    """Create and yield an approved non-admin test user."""
    with app.app_context():
        user = User(name='Test User', email='testuser@example.com',
                    is_approved=True, is_admin=False)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def auth_client(client, approved_user):
    """Test client logged in as the approved user."""
    client.post('/auth/login', data={
        'email': 'testuser@example.com',
        'password': 'password123',
    }, follow_redirects=True)
    return client


# ── Shop button styling ────────────────────────────────────────────────────────

class TestShopNavButtonStyling:
    def test_shop_text_in_navbar(self, client):
        assert '>Shop<' in _navbar_html(client)

    def test_blue_background_class(self, client):
        assert 'bg-blue-500' in _shop_anchor(client)

    def test_blue_hover_class(self, client):
        assert 'hover:bg-blue-600' in _shop_anchor(client)

    def test_white_text_class(self, client):
        assert 'text-white' in _shop_anchor(client)

    def test_font_medium_class(self, client):
        assert 'font-medium' in _shop_anchor(client)

    def test_rounded_pill_shape(self, client):
        assert 'rounded-lg' in _shop_anchor(client)

    def test_padding_applied(self, client):
        anchor = _shop_anchor(client)
        assert 'px-3' in anchor and 'py-1.5' in anchor

    def test_transition_class_for_hover(self, client):
        assert 'transition' in _shop_anchor(client)


# ── Mobile visibility ──────────────────────────────────────────────────────────

class TestShopNavButtonVisibility:
    def test_hidden_on_mobile_class_present(self, client):
        """Button must be hidden below sm breakpoint via 'hidden sm:inline'."""
        anchor = _shop_anchor(client)
        assert 'hidden' in anchor
        assert 'sm:inline' in anchor

    def test_not_a_plain_text_link(self, client):
        """Button must carry pill classes, not be an unstyled anchor."""
        anchor = _shop_anchor(client)
        assert 'bg-blue-500' in anchor, "Shop link is missing pill button class"


# ── Navigation target ──────────────────────────────────────────────────────────

class TestShopNavButtonNavigation:
    def test_href_points_to_products(self, client):
        assert '/products' in _shop_anchor(client)

    def test_products_page_returns_200(self, client):
        resp = client.get('/products')
        assert resp.status_code == 200

    def test_products_page_also_has_shop_button(self, client):
        """Shop button must render on the products listing page too."""
        assert '>Shop<' in _navbar_html(client, '/products')


# ── Consistency across pages extending base.html ───────────────────────────────

class TestShopNavButtonConsistency:
    def test_shop_button_on_homepage(self, client):
        assert 'bg-blue-500' in _shop_anchor(client, '/')

    def test_shop_button_on_products_page(self, client):
        assert 'bg-blue-500' in _shop_anchor(client, '/products')

    def test_shop_button_href_consistent_across_pages(self, client):
        href_home = _shop_anchor(client, '/')
        href_products = _shop_anchor(client, '/products')
        assert '/products' in href_home
        assert '/products' in href_products


# ── Visual distinction: Shop (blue) vs +Sell (green) ─────────────────────────

class TestShopVsSellDistinction:
    def test_shop_button_is_blue(self, client):
        assert 'bg-blue-500' in _shop_anchor(client)

    def test_sell_button_is_green_for_authenticated_user(self, auth_client):
        nav = _navbar_html(auth_client)
        # +Sell button uses green background
        assert 'bg-green-600' in nav

    def test_shop_and_sell_buttons_coexist(self, auth_client):
        nav = _navbar_html(auth_client)
        assert '>Shop<' in nav
        assert '+ Sell' in nav or '>+ Sell<' in nav

    def test_shop_not_green(self, client):
        anchor = _shop_anchor(client)
        assert 'bg-green-600' not in anchor
        assert 'bg-green-700' not in anchor

    def test_sell_not_blue(self, auth_client):
        nav = _navbar_html(auth_client)
        sell_pos = nav.index('+ Sell')
        a_start = nav.rindex('<a ', 0, sell_pos)
        a_end = nav.index('>', a_start) + 1
        sell_anchor = nav[a_start:a_end]
        assert 'bg-blue-500' not in sell_anchor
