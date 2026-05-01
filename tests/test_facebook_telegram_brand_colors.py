"""
Tests for Facebook and Telegram brand-color styling in the footer.
Change: Facebook (#1877f2 solid blue) and Telegram (#29a8e4 solid blue) get full
brand colors as solid backgrounds; Instagram retains neutral grey (#4b5563).
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


# ── Facebook brand color ───────────────────────────────────────────────────────

class TestFacebookBrandColor:
    def test_facebook_solid_blue_background(self, client):
        assert '#1877f2' in _facebook(_html(client))

    def test_facebook_white_text(self, client):
        section = _facebook(_html(client))
        assert 'color:#fff' in section

    def test_facebook_hover_darkens(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#145dbf'" in section or 'backgroundColor="#145dbf"' in section

    def test_facebook_mouseout_reverts_to_brand(self, client):
        section = _facebook(_html(client))
        assert "backgroundColor='#1877f2'" in section or 'backgroundColor="#1877f2"' in section

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


# ── Telegram brand color ───────────────────────────────────────────────────────

class TestTelegramBrandColor:
    def test_telegram_solid_blue_background(self, client):
        assert '#29a8e4' in _telegram(_html(client))

    def test_telegram_white_text(self, client):
        section = _telegram(_html(client))
        assert 'color:#fff' in section

    def test_telegram_hover_darkens(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#1e8bbf'" in section or 'backgroundColor="#1e8bbf"' in section

    def test_telegram_mouseout_reverts_to_brand(self, client):
        section = _telegram(_html(client))
        assert "backgroundColor='#29a8e4'" in section or 'backgroundColor="#29a8e4"' in section

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


# ── Instagram remains neutral grey ────────────────────────────────────────────

class TestInstagramRemainsGrey:
    def test_instagram_grey_background(self, client):
        assert '#4b5563' in _instagram(_html(client))

    def test_instagram_white_text(self, client):
        assert 'color:#fff' in _instagram(_html(client))

    def test_instagram_hover_darkens_grey(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#374151'" in section or 'backgroundColor="#374151"' in section

    def test_instagram_mouseout_reverts_to_grey(self, client):
        section = _instagram(_html(client))
        assert "backgroundColor='#4b5563'" in section or 'backgroundColor="#4b5563"' in section

    def test_instagram_not_facebook_blue(self, client):
        section = _instagram(_html(client))
        assert '#1877f2' not in section

    def test_instagram_not_telegram_blue(self, client):
        section = _instagram(_html(client))
        assert '#29a8e4' not in section

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


# ── All three buttons present ──────────────────────────────────────────────────

class TestAllThreeButtonsPresent:
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

    def test_flex_gap_container_present(self, client):
        html = _html(client)
        footer = html[html.index('<footer'):html.index('</footer>')]
        assert 'flex items-center gap-' in footer

    def test_instagram_visually_distinct_from_facebook(self, client):
        html = _html(client)
        fb = _facebook(html)
        ig = _instagram(html)
        fb_bg = fb[fb.index('background-color:'):fb.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert fb_bg != ig_bg

    def test_instagram_visually_distinct_from_telegram(self, client):
        html = _html(client)
        tg = _telegram(html)
        ig = _instagram(html)
        tg_bg = tg[tg.index('background-color:'):tg.index('background-color:') + 30]
        ig_bg = ig[ig.index('background-color:'):ig.index('background-color:') + 30]
        assert tg_bg != ig_bg
