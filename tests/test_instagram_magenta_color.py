"""
Tests for the Instagram button color change: green → magenta/pink.
PR summary: background changed from #0a2a0f to #3d0c20,
icon/text color changed from #22c55e to #e1306c,
hover fill changed from #22c55e to #e1306c with white text.
"""


def _html(client):
    resp = client.get('/')
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _instagram_anchor(html):
    url = 'https://instagram.com/styleus'
    url_pos = html.index(url)
    a_start = html.rindex('<a ', 0, url_pos)
    tag_end = html.index('>', url_pos) + 1
    return html[a_start:tag_end]


def _facebook_anchor(html):
    url = 'https://facebook.com/styleus'
    url_pos = html.index(url)
    a_start = html.rindex('<a ', 0, url_pos)
    tag_end = html.index('>', url_pos) + 1
    return html[a_start:tag_end]


def _telegram_anchor(html):
    url = 'https://t.me/LaptopSoft'
    url_pos = html.index(url)
    a_start = html.rindex('<a ', 0, url_pos)
    tag_end = html.index('>', url_pos) + 1
    return html[a_start:tag_end]


class TestInstagramMagentaColor:
    def test_magenta_icon_color_present(self, client):
        assert '#e1306c' in _instagram_anchor(_html(client))

    def test_dark_magenta_resting_background(self, client):
        assert '#3d0c20' in _instagram_anchor(_html(client))

    def test_hover_fills_magenta(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#e1306c'" in section or 'backgroundColor="#e1306c"' in section

    def test_mouseout_reverts_to_dark_magenta(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#3d0c20'" in section or 'backgroundColor="#3d0c20"' in section

    def test_old_green_color_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert '#22c55e' not in section

    def test_old_green_background_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert '#0a2a0f' not in section

    def test_instagram_url_correct(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_instagram_opens_new_tab(self, client):
        assert 'target="_blank"' in _instagram_anchor(_html(client))

    def test_instagram_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _instagram_anchor(_html(client))

    def test_instagram_aria_label(self, client):
        assert 'aria-label="Instagram"' in _instagram_anchor(_html(client))

    def test_instagram_label_text_present(self, client):
        assert '>Instagram<' in _html(client)

    def test_instagram_pill_shape(self, client):
        assert 'rounded-full' in _instagram_anchor(_html(client))

    def test_instagram_rendered_in_footer(self, client):
        html = _html(client)
        footer_start = html.index('<footer')
        footer_end = html.index('</footer>')
        footer_html = html[footer_start:footer_end]
        assert 'https://instagram.com/styleus' in footer_html

    def test_instagram_not_purple(self, client):
        section = _instagram_anchor(_html(client))
        assert '#833ab4' not in section


class TestUnaffectedButtons:
    def test_facebook_brand_color_unchanged(self, client):
        section = _facebook_anchor(_html(client))
        assert '#1877f2' in section

    def test_facebook_background_unchanged(self, client):
        section = _facebook_anchor(_html(client))
        assert '#1a2744' in section

    def test_facebook_hover_unchanged(self, client):
        section = _facebook_anchor(_html(client))
        assert "backgroundColor='#1877f2'" in section or 'backgroundColor="#1877f2"' in section

    def test_telegram_brand_color_unchanged(self, client):
        section = _telegram_anchor(_html(client))
        assert '#29a8e4' in section

    def test_telegram_background_unchanged(self, client):
        section = _telegram_anchor(_html(client))
        assert '#1e3a5f' in section

    def test_telegram_hover_unchanged(self, client):
        section = _telegram_anchor(_html(client))
        assert "backgroundColor='#29a8e4'" in section or 'backgroundColor="#29a8e4"' in section
