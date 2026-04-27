"""
Tests for the footer social-link pill buttons (Facebook, Instagram, Telegram).
These verify the restyling change that made Facebook and Instagram render as
rounded-full badges matching the existing Telegram pill pattern.
"""


def _html(client):
    resp = client.get('/')
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _enclosing_anchor(html, url):
    """Return the full opening <a> tag that contains the given url."""
    url_pos = html.index(url)
    a_start = html.rindex('<a ', 0, url_pos)
    tag_end = html.index('>', url_pos) + 1
    return html[a_start: tag_end]


# ── Facebook ──────────────────────────────────────────────────────────────────

class TestFacebookPill:
    def test_link_url_present(self, client):
        assert 'https://facebook.com/styleus' in _html(client)

    def test_opens_new_tab(self, client):
        assert 'target="_blank"' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')

    def test_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')

    def test_label_text(self, client):
        assert '>Facebook<' in _html(client)

    def test_pill_shape(self, client):
        assert 'rounded-full' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')

    def test_brand_color_applied(self, client):
        assert '#1877f2' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')

    def test_dark_resting_background(self, client):
        assert '#1a2744' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')

    def test_hover_fills_brand_color(self, client):
        section = _enclosing_anchor(_html(client), 'https://facebook.com/styleus')
        # onmouseover sets background to brand colour
        assert "backgroundColor='#1877f2'" in section or 'backgroundColor="#1877f2"' in section

    def test_aria_label(self, client):
        assert 'aria-label="Facebook"' in _enclosing_anchor(_html(client), 'https://facebook.com/styleus')


# ── Instagram ─────────────────────────────────────────────────────────────────

class TestInstagramPill:
    def test_link_url_present(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_opens_new_tab(self, client):
        assert 'target="_blank"' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')

    def test_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')

    def test_label_text(self, client):
        assert '>Instagram<' in _html(client)

    def test_pill_shape(self, client):
        assert 'rounded-full' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')

    def test_brand_color_applied(self, client):
        assert '#22c55e' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')

    def test_dark_resting_background(self, client):
        assert '#0a2a0f' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')

    def test_hover_fills_brand_color(self, client):
        section = _enclosing_anchor(_html(client), 'https://instagram.com/styleus')
        assert "backgroundColor='#22c55e'" in section or 'backgroundColor="#22c55e"' in section

    def test_aria_label(self, client):
        assert 'aria-label="Instagram"' in _enclosing_anchor(_html(client), 'https://instagram.com/styleus')


# ── Telegram (unchanged) ──────────────────────────────────────────────────────

class TestTelegramPill:
    def test_link_url_present(self, client):
        assert 'https://t.me/LaptopSoft' in _html(client)

    def test_opens_new_tab(self, client):
        assert 'target="_blank"' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')

    def test_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')

    def test_label_text(self, client):
        assert '>Telegram<' in _html(client)

    def test_pill_shape_unchanged(self, client):
        assert 'rounded-full' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')

    def test_brand_color_unchanged(self, client):
        assert '#29a8e4' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')

    def test_dark_resting_background_unchanged(self, client):
        assert '#1e3a5f' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')

    def test_aria_label(self, client):
        assert 'aria-label="Telegram"' in _enclosing_anchor(_html(client), 'https://t.me/LaptopSoft')


# ── Cross-pill layout checks ──────────────────────────────────────────────────

class TestFooterLayout:
    def test_all_three_pills_present(self, client):
        html = _html(client)
        assert 'https://facebook.com/styleus' in html
        assert 'https://instagram.com/styleus' in html
        assert 'https://t.me/LaptopSoft' in html

    def test_pills_rendered_in_footer(self, client):
        html = _html(client)
        footer_start = html.index('<footer')
        footer_end = html.index('</footer>')
        footer_html = html[footer_start:footer_end]
        assert 'https://facebook.com/styleus' in footer_html
        assert 'https://instagram.com/styleus' in footer_html
        assert 'https://t.me/LaptopSoft' in footer_html

    def test_pills_have_gap_flex_container(self, client):
        html = _html(client)
        footer_start = html.index('<footer')
        footer_end = html.index('</footer>')
        footer_html = html[footer_start:footer_end]
        # The three pills share a flex container with gap
        assert 'flex items-center gap-' in footer_html

    def test_pills_have_icon_and_label(self, client):
        html = _html(client)
        # Each pill has an SVG icon + text label
        assert '>Facebook<' in html
        assert '>Instagram<' in html
        assert '>Telegram<' in html
