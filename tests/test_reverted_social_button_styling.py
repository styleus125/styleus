"""
Tests for the reverted Facebook and Telegram social button styling.
Commit 31883f4 reverted f9c427a, restoring:
  Facebook:  dark navy (#1a2744) background, blue (#1877f2) icon; hover → solid blue + white text
  Telegram:  dark blue (#1e3a5f) background, light blue (#29a8e4) icon; hover → solid light blue + white text
  Instagram: grey (#4b5563) background unchanged
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


# ── Smoke test ─────────────────────────────────────────────────────────────────

class TestSmokeHomePage:
    def test_home_page_returns_200(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_home_page_has_footer(self, client):
        html = _html(client)
        assert '<footer' in html and '</footer>' in html


# ── Facebook: reverted to dark navy background ─────────────────────────────────

class TestFacebookRevertedStyling:
    def test_facebook_dark_navy_background(self, client):
        assert 'background-color:#1a2744' in _facebook(_html(client))

    def test_facebook_blue_icon_color(self, client):
        section = _facebook(_html(client))
        assert 'color:#1877f2' in section

    def test_facebook_hover_turns_solid_blue(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1877f2'" in section or 'backgroundColor="#1877f2"' in section

    def test_facebook_hover_text_becomes_white(self, client):
        section = _facebook(_html(client))
        assert "this.style.color='#fff'" in section or "this.style.color=\"#fff\"" in section

    def test_facebook_mouseout_restores_navy(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1a2744'" in section or 'backgroundColor="#1a2744"' in section

    def test_facebook_mouseout_restores_blue_icon(self, client):
        section = _facebook(_html(client))
        assert "this.style.color='#1877f2'" in section or "this.style.color=\"#1877f2\"" in section

    def test_facebook_not_solid_blue_background(self, client):
        """After revert, background must NOT be solid #1877f2 in the style attribute."""
        section = _facebook(_html(client))
        assert 'background-color:#1877f2' not in section

    def test_facebook_url_correct(self, client):
        assert 'https://facebook.com/styleus' in _html(client)

    def test_facebook_new_tab(self, client):
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


# ── Telegram: reverted to dark blue background ─────────────────────────────────

class TestTelegramRevertedStyling:
    def test_telegram_dark_blue_background(self, client):
        assert 'background-color:#1e3a5f' in _telegram(_html(client))

    def test_telegram_light_blue_icon_color(self, client):
        section = _telegram(_html(client))
        assert 'color:#29a8e4' in section

    def test_telegram_hover_turns_solid_light_blue(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#29a8e4'" in section or 'backgroundColor="#29a8e4"' in section

    def test_telegram_hover_text_becomes_white(self, client):
        section = _telegram(_html(client))
        assert "this.style.color='#fff'" in section or "this.style.color=\"#fff\"" in section

    def test_telegram_mouseout_restores_dark_blue(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#1e3a5f'" in section or 'backgroundColor="#1e3a5f"' in section

    def test_telegram_mouseout_restores_light_blue_icon(self, client):
        section = _telegram(_html(client))
        assert "this.style.color='#29a8e4'" in section or "this.style.color=\"#29a8e4\"" in section

    def test_telegram_not_solid_brand_background(self, client):
        """After revert, background must NOT be solid #29a8e4 in the style attribute."""
        section = _telegram(_html(client))
        assert 'background-color:#29a8e4' not in section

    def test_telegram_url_correct(self, client):
        assert 'https://t.me/LaptopSoft' in _html(client)

    def test_telegram_new_tab(self, client):
        assert 'target="_blank"' in _telegram(_html(client))

    def test_telegram_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _telegram(_html(client))

    def test_telegram_aria_label(self, client):
        assert 'aria-label="Telegram"' in _telegram(_html(client))

    def test_telegram_label_text(self, client):
        assert '>Telegram<' in _html(client)

    def test_telegram_pill_shape(self, client):
        assert 'rounded-full' in _telegram(_html(client))

    def test_telegram_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://t.me/LaptopSoft' in footer


# ── Instagram: unchanged grey ──────────────────────────────────────────────────

class TestInstagramUnchangedGrey:
    def test_instagram_grey_background(self, client):
        assert 'background-color:#4b5563' in _instagram(_html(client))

    def test_instagram_white_text(self, client):
        assert 'color:#fff' in _instagram(_html(client))

    def test_instagram_hover_darkens_grey(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#374151'" in section or 'backgroundColor="#374151"' in section

    def test_instagram_mouseout_reverts_grey(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#4b5563'" in section or 'backgroundColor="#4b5563"' in section

    def test_instagram_not_red(self, client):
        assert '#dc2626' not in _instagram(_html(client))

    def test_instagram_url_correct(self, client):
        assert 'https://instagram.com/styleus' in _html(client)

    def test_instagram_new_tab(self, client):
        assert 'target="_blank"' in _instagram(_html(client))

    def test_instagram_noopener_noreferrer(self, client):
        assert 'noopener noreferrer' in _instagram(_html(client))

    def test_instagram_aria_label(self, client):
        assert 'aria-label="Instagram"' in _instagram(_html(client))

    def test_instagram_label_text(self, client):
        assert '>Instagram<' in _html(client)

    def test_instagram_pill_shape(self, client):
        assert 'rounded-full' in _instagram(_html(client))

    def test_instagram_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://instagram.com/styleus' in footer


# ── All three buttons accessible ──────────────────────────────────────────────

class TestAllSocialButtonsAccessible:
    def test_all_urls_present(self, client):
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
        fb = _facebook(html)
        ig = _instagram(html)
        tg = _telegram(html)
        assert 'target="_blank"' in fb
        assert 'target="_blank"' in ig
        assert 'target="_blank"' in tg

    def test_all_in_footer(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'https://facebook.com/styleus' in footer
        assert 'https://instagram.com/styleus' in footer
        assert 'https://t.me/LaptopSoft' in footer

    def test_facebook_distinct_from_instagram(self, client):
        html = _html(client)
        fb = _facebook(html)
        ig = _instagram(html)
        fb_bg = fb[fb.index('background-color:'):fb.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert fb_bg != ig_bg

    def test_telegram_distinct_from_instagram(self, client):
        html = _html(client)
        tg = _telegram(html)
        ig = _instagram(html)
        tg_bg = tg[tg.index('background-color:'):tg.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert tg_bg != ig_bg
