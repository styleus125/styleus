"""
Tests for the favicon addition:
- static/favicon.svg exists and is served correctly
- <link rel="icon"> appears in <head> of public pages (base.html)
- <link rel="icon"> appears in <head> of admin pages (admin/base.html)
"""
import pytest
from models import db, User


# ── Helpers ───────────────────────────────────────────────────────────────────

def _html(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _head_html(client, path):
    html = _html(client, path)
    head_end = html.index('</head>')
    return html[:head_end]


def _favicon_link_tag(client, path):
    """Return the <link rel="icon"> tag from the <head> of the given page."""
    head = _head_html(client, path)
    try:
        pos = head.index('rel="icon"')
    except ValueError:
        return None
    tag_start = head.rindex('<link', 0, pos)
    tag_end = head.index('>', tag_start) + 1
    return head[tag_start:tag_end]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(app):
    with app.app_context():
        user = User(name='Admin User', email='admintest@example.com',
                    is_approved=True, is_admin=True)
        user.set_password('adminpass123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def admin_client(client, admin_user):
    client.post('/auth/login', data={
        'email': 'admintest@example.com',
        'password': 'adminpass123',
    }, follow_redirects=True)
    return client


# ── favicon.svg static file ───────────────────────────────────────────────────

class TestFaviconSVGFile:
    def test_favicon_svg_returns_200(self, client):
        resp = client.get('/static/favicon.svg')
        assert resp.status_code == 200

    def test_favicon_svg_content_type_is_svg(self, client):
        resp = client.get('/static/favicon.svg')
        assert 'svg' in resp.content_type.lower()

    def test_favicon_svg_contains_svg_tag(self, client):
        resp = client.get('/static/favicon.svg')
        content = resp.data.decode('utf-8')
        assert '<svg' in content

    def test_favicon_svg_has_blue_fill(self, client):
        resp = client.get('/static/favicon.svg')
        content = resp.data.decode('utf-8')
        assert '#3b82f6' in content

    def test_favicon_svg_contains_letter_s(self, client):
        resp = client.get('/static/favicon.svg')
        content = resp.data.decode('utf-8')
        assert '>S<' in content

    def test_favicon_svg_has_correct_viewbox(self, client):
        resp = client.get('/static/favicon.svg')
        content = resp.data.decode('utf-8')
        assert 'viewBox="0 0 40 40"' in content


# ── Public pages (base.html) ──────────────────────────────────────────────────

class TestFaviconLinkPublicPages:
    def test_homepage_has_favicon_link(self, client):
        tag = _favicon_link_tag(client, '/')
        assert tag is not None, '<link rel="icon"> missing from homepage <head>'

    def test_products_page_has_favicon_link(self, client):
        tag = _favicon_link_tag(client, '/products')
        assert tag is not None, '<link rel="icon"> missing from products page <head>'

    def test_favicon_link_type_is_svg_xml(self, client):
        tag = _favicon_link_tag(client, '/')
        assert 'type="image/svg+xml"' in tag

    def test_favicon_href_points_to_favicon_svg(self, client):
        tag = _favicon_link_tag(client, '/')
        assert 'favicon.svg' in tag

    def test_favicon_link_is_in_head_not_body(self, client):
        html = _html(client, '/')
        head_end = html.index('</head>')
        favicon_pos = html.index('rel="icon"')
        assert favicon_pos < head_end, '<link rel="icon"> must appear before </head>'

    def test_favicon_href_is_static_url(self, client):
        tag = _favicon_link_tag(client, '/')
        assert '/static/' in tag


# ── Admin pages (admin/base.html) ─────────────────────────────────────────────

class TestFaviconLinkAdminPages:
    def test_admin_dashboard_has_favicon_link(self, admin_client):
        tag = _favicon_link_tag(admin_client, '/admin/')
        assert tag is not None, '<link rel="icon"> missing from admin dashboard <head>'

    def test_admin_favicon_type_is_svg_xml(self, admin_client):
        tag = _favicon_link_tag(admin_client, '/admin/')
        assert 'type="image/svg+xml"' in tag

    def test_admin_favicon_href_points_to_favicon_svg(self, admin_client):
        tag = _favicon_link_tag(admin_client, '/admin/')
        assert 'favicon.svg' in tag

    def test_admin_favicon_link_is_in_head_not_body(self, admin_client):
        resp = admin_client.get('/admin/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        head_end = html.index('</head>')
        favicon_pos = html.index('rel="icon"')
        assert favicon_pos < head_end

    def test_admin_favicon_same_file_as_public(self, client, admin_client):
        public_tag = _favicon_link_tag(client, '/')
        admin_tag = _favicon_link_tag(admin_client, '/admin/')
        # Both should reference the same favicon.svg file
        assert 'favicon.svg' in public_tag
        assert 'favicon.svg' in admin_tag
