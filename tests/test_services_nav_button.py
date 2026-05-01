"""
Tests for the Services navbar link restyling change.
The plain text anchor was replaced with a purple pill button
(bg-purple-600 hover:bg-purple-700) matching the Shop button pattern.
"""

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


def _services_anchor(client, path='/'):
    """Return the full opening <a> tag for the Services nav link."""
    nav = _navbar_html(client, path)
    services_pos = nav.index('>Services<')
    a_start = nav.rindex('<a ', 0, services_pos)
    a_end = nav.index('>', a_start) + 1
    return nav[a_start:a_end]


def _shop_anchor(client, path='/'):
    """Return the full opening <a> tag for the Shop nav link."""
    nav = _navbar_html(client, path)
    shop_pos = nav.index('>Shop<')
    a_start = nav.rindex('<a ', 0, shop_pos)
    a_end = nav.index('>', a_start) + 1
    return nav[a_start:a_end]


# ── Services button styling ────────────────────────────────────────────────────

class TestServicesNavButtonStyling:
    def test_services_text_in_navbar(self, client):
        assert '>Services<' in _navbar_html(client)

    def test_purple_background_class(self, client):
        assert 'bg-purple-600' in _services_anchor(client)

    def test_purple_hover_class(self, client):
        assert 'hover:bg-purple-700' in _services_anchor(client)

    def test_white_text_class(self, client):
        assert 'text-white' in _services_anchor(client)

    def test_font_medium_class(self, client):
        assert 'font-medium' in _services_anchor(client)

    def test_rounded_pill_shape(self, client):
        assert 'rounded-lg' in _services_anchor(client)

    def test_padding_applied(self, client):
        anchor = _services_anchor(client)
        assert 'px-3' in anchor and 'py-1.5' in anchor

    def test_transition_class_for_hover(self, client):
        assert 'transition' in _services_anchor(client)


# ── Mobile visibility ──────────────────────────────────────────────────────────

class TestServicesNavButtonVisibility:
    def test_hidden_on_mobile_class_present(self, client):
        """Button must be hidden below sm breakpoint via 'hidden sm:inline'."""
        anchor = _services_anchor(client)
        assert 'hidden' in anchor
        assert 'sm:inline' in anchor

    def test_not_a_plain_text_link(self, client):
        """Button must carry pill classes, not be an unstyled anchor."""
        anchor = _services_anchor(client)
        assert 'bg-purple-600' in anchor, "Services link is missing pill button class"


# ── Navigation target ──────────────────────────────────────────────────────────

class TestServicesNavButtonNavigation:
    def test_href_points_to_services(self, client):
        assert '/services' in _services_anchor(client)

    def test_services_page_returns_200(self, client):
        resp = client.get('/services')
        assert resp.status_code == 200

    def test_services_page_also_has_services_button(self, client):
        """Services button must render on the services page too."""
        assert '>Services<' in _navbar_html(client, '/services')


# ── Shop button unaffected ─────────────────────────────────────────────────────

class TestShopButtonUnaffected:
    def test_shop_button_still_blue(self, client):
        assert 'bg-blue-500' in _shop_anchor(client)

    def test_shop_hover_still_blue(self, client):
        assert 'hover:bg-blue-600' in _shop_anchor(client)

    def test_shop_not_purple(self, client):
        anchor = _shop_anchor(client)
        assert 'bg-purple-600' not in anchor
        assert 'bg-purple-700' not in anchor


# ── Visual distinction: Services (purple) vs Shop (blue) ──────────────────────

class TestServicesVsShopDistinction:
    def test_services_button_is_purple(self, client):
        assert 'bg-purple-600' in _services_anchor(client)

    def test_shop_button_is_blue(self, client):
        assert 'bg-blue-500' in _shop_anchor(client)

    def test_services_not_blue(self, client):
        anchor = _services_anchor(client)
        assert 'bg-blue-500' not in anchor

    def test_shop_and_services_coexist_in_navbar(self, client):
        nav = _navbar_html(client)
        assert '>Shop<' in nav
        assert '>Services<' in nav


# ── Consistency across pages extending base.html ───────────────────────────────

class TestServicesNavButtonConsistency:
    def test_services_button_on_homepage(self, client):
        assert 'bg-purple-600' in _services_anchor(client, '/')

    def test_services_button_on_products_page(self, client):
        assert 'bg-purple-600' in _services_anchor(client, '/products')

    def test_services_href_consistent_across_pages(self, client):
        href_home = _services_anchor(client, '/')
        href_products = _services_anchor(client, '/products')
        assert '/services' in href_home
        assert '/services' in href_products


# ── Smoke tests ────────────────────────────────────────────────────────────────

class TestSmokeTests:
    def test_homepage_returns_200(self, client):
        assert client.get('/').status_code == 200

    def test_admin_returns_302_when_unauthenticated(self, client):
        assert client.get('/admin/').status_code == 302
