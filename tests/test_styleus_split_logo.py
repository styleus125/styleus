"""
Tests for the Styleus split text logo change.
The SVG image logo was replaced with inline HTML:
  <span class="text-white">Style</span><span class="text-blue-400">us</span>
across navbar, footer, and admin sidebar.
"""
import pytest
from models import db, User


# ── Helpers ───────────────────────────────────────────────────────────────────

def _html(client, path='/'):
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _navbar_html(client, path='/'):
    html = _html(client, path)
    nav_start = html.index('<nav ')
    nav_end = html.index('</nav>') + len('</nav>')
    return html[nav_start:nav_end]


def _footer_html(client, path='/'):
    html = _html(client, path)
    footer_start = html.index('<footer ')
    footer_end = html.index('</footer>') + len('</footer>')
    return html[footer_start:footer_end]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(
            name='Admin User',
            email='admin_logo_test@example.com',
            is_approved=True,
            is_admin=True,
        )
        user.set_password('adminpass123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def admin_client(client, admin_user):
    client.post('/auth/login', data={
        'email': 'admin_logo_test@example.com',
        'password': 'adminpass123',
    }, follow_redirects=True)
    return client


# ── Navbar logo ───────────────────────────────────────────────────────────────

class TestNavbarSplitLogo:
    def test_style_span_white_in_navbar(self, client):
        """'Style' part must use text-white class."""
        nav = _navbar_html(client)
        assert '<span class="text-white">Style</span>' in nav

    def test_us_span_blue_in_navbar(self, client):
        """'us' part must use text-blue-400 class."""
        nav = _navbar_html(client)
        assert '<span class="text-blue-400">us</span>' in nav

    def test_navbar_logo_bold_text(self, client):
        """Outer span must carry font-bold and tracking-tight."""
        nav = _navbar_html(client)
        assert 'font-bold' in nav
        assert 'tracking-tight' in nav

    def test_navbar_logo_select_none(self, client):
        nav = _navbar_html(client)
        assert 'select-none' in nav

    def test_navbar_logo_link_points_to_shop_index(self, client):
        """Navbar logo anchor must link to the shop index (/)."""
        nav = _navbar_html(client)
        logo_pos = nav.index('<span class="text-white">Style</span>')
        a_start = nav.rindex('<a ', 0, logo_pos)
        a_end = nav.index('>', a_start) + 1
        logo_anchor = nav[a_start:a_end]
        assert 'href="/"' in logo_anchor or 'href=/' in logo_anchor

    def test_navbar_logo_on_products_page(self, client):
        """Split logo must appear on every page extending base.html."""
        nav = _navbar_html(client, '/products')
        assert '<span class="text-white">Style</span>' in nav
        assert '<span class="text-blue-400">us</span>' in nav

    def test_navbar_logo_text_size(self, client):
        """Navbar outer span must use text-2xl."""
        nav = _navbar_html(client)
        assert 'text-2xl' in nav

    def test_navbar_logo_on_mobile_class_select_none(self, client):
        """select-none prevents text selection on mobile tap."""
        nav = _navbar_html(client)
        assert 'select-none' in nav


# ── Footer logo ───────────────────────────────────────────────────────────────

class TestFooterSplitLogo:
    def test_style_span_white_in_footer(self, client):
        footer = _footer_html(client)
        assert '<span class="text-white">Style</span>' in footer

    def test_us_span_blue_in_footer(self, client):
        footer = _footer_html(client)
        assert '<span class="text-blue-400">us</span>' in footer

    def test_footer_logo_bold_text(self, client):
        footer = _footer_html(client)
        assert 'font-bold' in footer
        assert 'tracking-tight' in footer

    def test_footer_logo_link_points_to_shop_index(self, client):
        """Footer logo anchor must link to the shop index (/)."""
        footer = _footer_html(client)
        logo_pos = footer.index('<span class="text-white">Style</span>')
        a_start = footer.rindex('<a ', 0, logo_pos)
        a_end = footer.index('>', a_start) + 1
        logo_anchor = footer[a_start:a_end]
        assert 'href="/"' in logo_anchor or 'href=/' in logo_anchor

    def test_footer_logo_text_size(self, client):
        """Footer logo must use text-xl (slightly smaller than navbar's text-2xl)."""
        footer = _footer_html(client)
        assert 'text-xl' in footer

    def test_footer_select_none(self, client):
        footer = _footer_html(client)
        assert 'select-none' in footer


# ── Admin sidebar logo ────────────────────────────────────────────────────────

class TestAdminSidebarSplitLogo:
    def _sidebar_html(self, admin_client):
        html = _html(admin_client, '/admin/')
        aside_start = html.index('<aside ')
        aside_end = html.index('</aside>') + len('</aside>')
        return html[aside_start:aside_end]

    def test_style_span_white_in_admin_sidebar(self, admin_client):
        sidebar = self._sidebar_html(admin_client)
        assert '<span class="text-white">Style</span>' in sidebar

    def test_us_span_blue_in_admin_sidebar(self, admin_client):
        sidebar = self._sidebar_html(admin_client)
        assert '<span class="text-blue-400">us</span>' in sidebar

    def test_admin_label_next_to_logo(self, admin_client):
        """'Admin' text must appear near the split logo in the sidebar."""
        sidebar = self._sidebar_html(admin_client)
        assert 'Admin' in sidebar

    def test_admin_sidebar_logo_link_points_to_dashboard(self, admin_client):
        """Admin sidebar logo must link to admin dashboard."""
        sidebar = self._sidebar_html(admin_client)
        logo_pos = sidebar.index('<span class="text-white">Style</span>')
        a_start = sidebar.rindex('<a ', 0, logo_pos)
        a_end = sidebar.index('>', a_start) + 1
        logo_anchor = sidebar[a_start:a_end]
        assert '/admin' in logo_anchor

    def test_admin_sidebar_logo_text_size(self, admin_client):
        """Admin sidebar logo uses text-lg."""
        sidebar = self._sidebar_html(admin_client)
        assert 'text-lg' in sidebar

    def test_admin_sidebar_bold_tracking(self, admin_client):
        sidebar = self._sidebar_html(admin_client)
        assert 'font-bold' in sidebar
        assert 'tracking-tight' in sidebar

    def test_admin_sidebar_select_none(self, admin_client):
        sidebar = self._sidebar_html(admin_client)
        assert 'select-none' in sidebar


# ── Navigation correctness ────────────────────────────────────────────────────

class TestLogoNavigation:
    def test_shop_index_returns_200(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_products_page_returns_200(self, client):
        resp = client.get('/products')
        assert resp.status_code == 200

    def test_admin_dashboard_returns_200_for_admin(self, admin_client):
        resp = admin_client.get('/admin/', follow_redirects=True)
        assert resp.status_code == 200

    def test_split_logo_consistent_across_shop_pages(self, client):
        """Both shop index and products page must show the split logo."""
        for path in ('/', '/products'):
            nav = _navbar_html(client, path)
            assert '<span class="text-white">Style</span>' in nav, f"Missing on {path}"
            assert '<span class="text-blue-400">us</span>' in nav, f"Missing on {path}"
