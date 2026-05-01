"""
Tests for Facebook button icon color change: blue (#1877f2) → yellow (#FFD700).
Resting: dark navy background (#1a2744), yellow icon/text (#FFD700).
Hover: yellow background (#FFD700), dark navy icon/text (#1a2744).
Mouse-out: reverts to dark navy background with yellow icon.
Instagram and Telegram buttons must remain unchanged.
"""


def _html(client):
    resp = client.get('/')
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _anchor(html, url):
    url_pos = html.index(url)
    a_start = html.rindex('<a ', 0, url_pos)
    tag_end = html.index('>', url_pos) + 1
    return html[a_start:tag_end]


def _facebook(html):
    return _anchor(html, 'https://facebook.com/styleus')


def _instagram(html):
    return _anchor(html, 'https://instagram.com/styleus')


def _telegram(html):
    return _anchor(html, 'https://t.me/LaptopSoft')


# ── Facebook yellow icon color (resting state) ─────────────────────────────────

class TestFacebookYellowColor:
    def test_yellow_icon_color_present(self, client):
        assert '#FFD700' in _facebook(_html(client)) or '#ffd700' in _facebook(_html(client)).lower()

    def test_resting_background_is_dark_navy(self, client):
        assert 'background-color:#1a2744' in _facebook(_html(client))

    def test_old_blue_icon_color_absent(self, client):
        section = _facebook(_html(client))
        assert '#1877f2' not in section

    def test_facebook_url_correct(self, client):
        assert 'https://facebook.com/styleus' in _html(client)

    def test_facebook_opens_new_tab(self, client):
        assert 'target="_blank"' in _facebook(_html(client))

    def test_facebook_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _facebook(_html(client))

    def test_facebook_aria_label(self, client):
        assert 'aria-label="Facebook"' in _facebook(_html(client))

    def test_facebook_label_text(self, client):
        assert '>Facebook<' in _html(client)

    def test_facebook_pill_shape(self, client):
        assert 'rounded-full' in _facebook(_html(client))

    def test_facebook_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://facebook.com/styleus' in footer


# ── Facebook hover state ───────────────────────────────────────────────────────

class TestFacebookHoverState:
    def test_hover_background_turns_yellow(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#FFD700'" in section or 'backgroundColor="#FFD700"' in section

    def test_hover_text_turns_dark_navy(self, client):
        section = _facebook(_html(client))
        assert "this.style.color='#1a2744'" in section or 'this.style.color="#1a2744"' in section

    def test_mouseout_restores_navy_background(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1a2744'" in section or 'backgroundColor="#1a2744"' in section

    def test_mouseout_restores_yellow_icon(self, client):
        section = _facebook(_html(client))
        # mouseout handler sets color back to yellow
        assert section.lower().count('#ffd700') >= 2


# ── Instagram unchanged ────────────────────────────────────────────────────────

class TestInstagramUnchanged:
    def test_instagram_black_background(self, client):
        assert 'background-color:#000000' in _instagram(_html(client))

    def test_instagram_white_text(self, client):
        assert 'color:#fff' in _instagram(_html(client))

    def test_instagram_hover_near_black(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#1a1a1a'" in section or 'backgroundColor="#1a1a1a"' in section

    def test_instagram_mouseout_reverts_to_black(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#000000'" in section or 'backgroundColor="#000000"' in section

    def test_instagram_not_yellow(self, client):
        section = _instagram(_html(client))
        assert '#FFD700' not in section and '#ffd700' not in section.lower()

    def test_instagram_url_correct(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_instagram_new_tab(self, client):
        assert 'target="_blank"' in _instagram(_html(client))


# ── Telegram unchanged ─────────────────────────────────────────────────────────

class TestTelegramUnchanged:
    def test_telegram_dark_blue_background(self, client):
        assert 'background-color:#1e3a5f' in _telegram(_html(client))

    def test_telegram_icon_color(self, client):
        assert '#29a8e4' in _telegram(_html(client))

    def test_telegram_hover_fills_brand_blue(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#29a8e4'" in section or 'backgroundColor="#29a8e4"' in section

    def test_telegram_mouseout_reverts(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#1e3a5f'" in section or 'backgroundColor="#1e3a5f"' in section

    def test_telegram_not_yellow(self, client):
        section = _telegram(_html(client))
        assert '#FFD700' not in section and '#ffd700' not in section.lower()

    def test_telegram_url_correct(self, client):
        assert 'https://t.me/LaptopSoft' in _html(client)

    def test_telegram_new_tab(self, client):
        assert 'target="_blank"' in _telegram(_html(client))


# ── All three buttons present ──────────────────────────────────────────────────

class TestAllSocialButtonsPresent:
    def test_all_urls_in_page(self, client):
        html = _html(client)
        assert 'https://facebook.com/styleus' in html
        assert 'https://instagram.com/styleus' in html
        assert 'https://t.me/LaptopSoft' in html

    def test_all_labels_present(self, client):
        html = _html(client)
        assert '>Facebook<' in html
        assert '>Instagram<' in html
        assert '>Telegram<' in html

    def test_all_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://facebook.com/styleus' in footer
        assert 'https://instagram.com/styleus' in footer
        assert 'https://t.me/LaptopSoft' in footer

    def test_facebook_visually_distinct_from_instagram(self, client):
        html = _html(client)
        fb = _facebook(html)
        ig = _instagram(html)
        fb_bg = fb[fb.index('background-color:'):fb.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert fb_bg != ig_bg

    def test_facebook_visually_distinct_from_telegram(self, client):
        html = _html(client)
        fb = _facebook(html)
        tg = _telegram(html)
        fb_bg = fb[fb.index('background-color:'):fb.index('background-color:') + 30]
        tg_bg = tg[tg.index('background-color:'):tg.index('background-color:') + 30]
        assert fb_bg != tg_bg
