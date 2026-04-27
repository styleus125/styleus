"""
Tests for the Instagram button color change: purple → green.
PR summary: background changed from #1a0f2e to #0a2a0f,
icon/text color changed from #833ab4 to #22c55e,
hover fill changed from #833ab4 to #22c55e.
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


class TestInstagramGreenColor:
    def test_green_icon_color_present(self, client):
        assert '#22c55e' in _instagram_anchor(_html(client))

    def test_dark_green_resting_background(self, client):
        assert '#0a2a0f' in _instagram_anchor(_html(client))

    def test_hover_fills_green(self, client):
        section = _instagram_anchor(_html(client))
        assert "backgroundColor='#22c55e'" in section or 'backgroundColor="#22c55e"' in section

    def test_old_purple_color_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert '#833ab4' not in section

    def test_old_purple_background_absent(self, client):
        section = _instagram_anchor(_html(client))
        assert '#1a0f2e' not in section

    def test_instagram_url_correct(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_instagram_opens_new_tab(self, client):
        assert 'target="_blank"' in _instagram_anchor(_html(client))

    def test_instagram_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _instagram_anchor(_html(client))

    def test_instagram_aria_label(self, client):
        assert 'aria-label="Instagram"' in _instagram_anchor(_html(client))

    def test_instagram_label_text(self, client):
        assert '>Instagram<' in _html(client)


class TestUnaffectedButtons:
    def test_facebook_color_unchanged(self, client):
        section = _facebook_anchor(_html(client))
        assert '#1877f2' in section

    def test_facebook_background_unchanged(self, client):
        section = _facebook_anchor(_html(client))
        assert '#1a2744' in section

    def test_telegram_color_unchanged(self, client):
        section = _telegram_anchor(_html(client))
        assert '#29a8e4' in section

    def test_telegram_background_unchanged(self, client):
        section = _telegram_anchor(_html(client))
        assert '#1e3a5f' in section
