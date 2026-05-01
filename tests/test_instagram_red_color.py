"""
Tests for the Instagram button color change: grey (#4b5563) → red (#dc2626).
PR summary: background changed to #dc2626, hover darkens to #b91c1c, text/icon stays white.
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


class TestInstagramRedColor:
    def test_red_background_present(self, client):
        assert '#dc2626' in _instagram_anchor(_html(client))

    def test_white_text_color_present(self, client):
        section = _instagram_anchor(_html(client))
        assert 'color:#fff' in section or "color: #fff" in section

    def test_hover_darkens_to_dark_red(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#b91c1c'" in section or 'backgroundColor="#b91c1c"' in section

    def test_hover_keeps_white_text(self, client):
        section = _instagram_anchor(_html(client))
        assert "this.style.color='#fff'" in section or 'this.style.color="#fff"' in section

    def test_mouseout_reverts_to_red(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#dc2626'" in section or 'backgroundColor="#dc2626"' in section

    def test_mouseout_keeps_white_text(self, client):
        section = _instagram_anchor(_html(client))
        count = section.count('#fff')
        assert count >= 2

    def test_old_grey_background_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert 'background-color:#4b5563' not in section
        assert "backgroundColor='#4b5563'" not in section
        assert 'backgroundColor="#4b5563"' not in section

    def test_old_grey_hover_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#374151'" not in section
        assert 'backgroundColor="#374151"' not in section

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
