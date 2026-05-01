"""
Tests for the Instagram button color change: grey (#4b5563) → black (#000000).
PR summary: background changed to #000000, hover darkens to #1a1a1a, mouseout
reverts to #000000; text/icon stays white. Facebook and Telegram unchanged.
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


def _instagram(html):
    return _anchor(html, 'https://instagram.com/styleus')


def _facebook(html):
    return _anchor(html, 'https://facebook.com/styleus')


def _telegram(html):
    return _anchor(html, 'https://t.me/LaptopSoft')


# ── Instagram black background ─────────────────────────────────────────────────

class TestInstagramBlackColor:
    def test_black_background_present(self, client):
        assert 'background-color:#000000' in _instagram(_html(client))

    def test_white_text_color_present(self, client):
        section = _instagram(_html(client))
        assert 'color:#fff' in section

    def test_hover_darkens_to_near_black(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#1a1a1a'" in section or 'backgroundColor="#1a1a1a"' in section

    def test_hover_keeps_white_text(self, client):
        section = _instagram(_html(client))
        assert "this.style.color='#fff'" in section or "this.style.color=\"#fff\"" in section

    def test_mouseout_reverts_to_black(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#000000'" in section or 'backgroundColor="#000000"' in section

    def test_mouseout_keeps_white_text(self, client):
        section = _instagram(_html(client))
        # white color set at least in resting style + mouseout handler
        assert section.count('#fff') >= 2

    def test_old_grey_background_absent(self, client):
        section = _instagram(_html(client))
        assert 'background-color:#4b5563' not in section
        assert "backgroundColor='#4b5563'" not in section
        assert 'backgroundColor="#4b5563"' not in section

    def test_old_grey_hover_absent(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#374151'" not in section
        assert 'backgroundColor="#374151"' not in section

    def test_instagram_url_correct(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_instagram_opens_new_tab(self, client):
        assert 'target="_blank"' in _instagram(_html(client))

    def test_instagram_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _instagram(_html(client))

    def test_instagram_aria_label(self, client):
        assert 'aria-label="Instagram"' in _instagram(_html(client))

    def test_instagram_label_text_present(self, client):
        assert '>Instagram<' in _html(client)

    def test_instagram_pill_shape(self, client):
        assert 'rounded-full' in _instagram(_html(client))

    def test_instagram_rendered_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://instagram.com/styleus' in footer


# ── Facebook and Telegram unchanged ───────────────────────────────────────────

class TestUnaffectedButtons:
    def test_facebook_dark_navy_background(self, client):
        assert 'background-color:#1a2744' in _facebook(_html(client))

    def test_facebook_blue_icon_color(self, client):
        assert '#1877f2' in _facebook(_html(client))

    def test_facebook_hover_unchanged(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1877f2'" in section or 'backgroundColor="#1877f2"' in section

    def test_facebook_mouseout_restores_navy(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1a2744'" in section or 'backgroundColor="#1a2744"' in section

    def test_telegram_dark_blue_background(self, client):
        assert 'background-color:#1e3a5f' in _telegram(_html(client))

    def test_telegram_light_blue_icon_color(self, client):
        assert '#29a8e4' in _telegram(_html(client))

    def test_telegram_hover_unchanged(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#29a8e4'" in section or 'backgroundColor="#29a8e4"' in section

    def test_telegram_mouseout_restores_dark_blue(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#1e3a5f'" in section or 'backgroundColor="#1e3a5f"' in section

    def test_facebook_url_correct(self, client):
        assert 'https://facebook.com/styleus' in _html(client)

    def test_telegram_url_correct(self, client):
        assert 'https://t.me/LaptopSoft' in _html(client)

    def test_facebook_new_tab(self, client):
        assert 'target="_blank"' in _facebook(_html(client))

    def test_telegram_new_tab(self, client):
        assert 'target="_blank"' in _telegram(_html(client))

    def test_facebook_aria_label(self, client):
        assert 'aria-label="Facebook"' in _facebook(_html(client))

    def test_telegram_aria_label(self, client):
        assert 'aria-label="Telegram"' in _telegram(_html(client))


# ── All three buttons present and accessible ───────────────────────────────────

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

    def test_all_aria_labels_present(self, client):
        html = _html(client)
        assert 'aria-label="Facebook"' in html
        assert 'aria-label="Instagram"' in html
        assert 'aria-label="Telegram"' in html

    def test_all_open_new_tab(self, client):
        html = _html(client)
        assert 'target="_blank"' in _facebook(html)
        assert 'target="_blank"' in _instagram(html)
        assert 'target="_blank"' in _telegram(html)

    def test_all_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://facebook.com/styleus' in footer
        assert 'https://instagram.com/styleus' in footer
        assert 'https://t.me/LaptopSoft' in footer

    def test_instagram_distinct_from_facebook(self, client):
        html = _html(client)
        fb = _facebook(html)
        ig = _instagram(html)
        fb_bg = fb[fb.index('background-color:'):fb.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert fb_bg != ig_bg

    def test_instagram_distinct_from_telegram(self, client):
        html = _html(client)
        tg = _telegram(html)
        ig = _instagram(html)
        tg_bg = tg[tg.index('background-color:'):tg.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert tg_bg != ig_bg
