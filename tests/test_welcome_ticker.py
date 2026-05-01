"""
Tests for the top contact bar layout in templates/base.html.

Changes covered:
- Welcome to Styleus! pinned to extreme left (flex-shrink-0)
- Scrolling ticker fills centre with flex-1 (hidden sm:block)
- WhatsApp icon + phone number pinned to extreme right (flex-shrink-0)
- Layout uses justify-between (not justify-end)
- CSS @keyframes ticker-scroll animation and .ticker-track class
"""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_html(client, path='/'):
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.data.decode('utf-8')


def _contact_bar_html(client, path='/'):
    """Return the top contact bar section (before <nav)."""
    html = _get_html(client, path)
    # The contact bar is the first div; it ends where <nav begins
    bar_start = html.index('<!-- Top contact bar -->')
    nav_start = html.index('<nav ')
    return html[bar_start:nav_start]


def _style_block(client, path='/'):
    """Return the inline <style> block content."""
    html = _get_html(client, path)
    style_start = html.index('<style>')
    style_end = html.index('</style>') + len('</style>')
    return html[style_start:style_end]


# ── Welcome label ─────────────────────────────────────────────────────────────


class TestWelcomeLabel:
    def test_welcome_text_present(self, client):
        assert 'Welcome to Styleus!' in _contact_bar_html(client)

    def test_welcome_gold_color(self, client):
        """Welcome label must use gold color #FFD700."""
        bar = _contact_bar_html(client)
        assert '#FFD700' in bar

    def test_welcome_in_span_tag(self, client):
        bar = _contact_bar_html(client)
        welcome_pos = bar.index('Welcome to Styleus!')
        span_start = bar.rindex('<span', 0, welcome_pos)
        assert span_start != -1

    def test_welcome_flex_shrink_zero(self, client):
        """Welcome span must not shrink in the flex bar."""
        bar = _contact_bar_html(client)
        welcome_pos = bar.index('Welcome to Styleus!')
        span_start = bar.rindex('<span', 0, welcome_pos)
        span_tag = bar[span_start:bar.index('>', span_start) + 1]
        assert 'flex-shrink-0' in span_tag

    def test_welcome_font_semibold(self, client):
        bar = _contact_bar_html(client)
        welcome_pos = bar.index('Welcome to Styleus!')
        span_start = bar.rindex('<span', 0, welcome_pos)
        span_tag = bar[span_start:bar.index('>', span_start) + 1]
        assert 'font-semibold' in span_tag


# ── Ticker presence and content ───────────────────────────────────────────────


class TestTickerContent:
    def test_ticker_track_class_present(self, client):
        assert 'ticker-track' in _contact_bar_html(client)

    def test_ticker_free_shipping_message(self, client):
        assert 'Free shipping on orders over Rs.999' in _contact_bar_html(client)

    def test_ticker_exclusive_deals_message(self, client):
        assert 'Exclusive deals every week' in _contact_bar_html(client)

    def test_ticker_premium_quality_message(self, client):
        assert 'Premium quality guaranteed' in _contact_bar_html(client)

    def test_ticker_new_arrivals_message(self, client):
        assert 'New arrivals daily' in _contact_bar_html(client)

    def test_ticker_blue_color(self, client):
        """Ticker text must use blue color (#93c5fd)."""
        assert '#93c5fd' in _contact_bar_html(client)

    def test_ticker_messages_duplicated_for_seamless_loop(self, client):
        """Messages are duplicated in the DOM for a seamless loop."""
        bar = _contact_bar_html(client)
        assert bar.count('Free shipping on orders over Rs.999') >= 2


# ── Ticker mobile visibility ──────────────────────────────────────────────────


def _ticker_wrapper_tag(client, path='/'):
    """Return the opening tag of the outer wrapper div that clips the ticker."""
    bar = _contact_bar_html(client, path)
    # The outer wrapper has overflow-hidden; find it before ticker-track
    ticker_pos = bar.index('ticker-track')
    # Walk back past the inner div to the outer wrapper (overflow-hidden div)
    overflow_pos = bar.rindex('overflow-hidden', 0, ticker_pos)
    div_start = bar.rindex('<div', 0, overflow_pos + 1)
    div_end = bar.index('>', div_start) + 1
    return bar[div_start:div_end]


class TestTickerMobileVisibility:
    def test_ticker_div_hidden_on_mobile(self, client):
        """Ticker wrapper must carry 'hidden' (hidden by default on mobile)."""
        assert 'hidden' in _ticker_wrapper_tag(client)

    def test_ticker_div_visible_on_sm_and_up(self, client):
        """Ticker wrapper must carry 'sm:block' to appear on sm+ screens."""
        assert 'sm:block' in _ticker_wrapper_tag(client)

    def test_ticker_overflow_hidden(self, client):
        """Ticker wrapper needs overflow-hidden to clip the scrolling text."""
        assert 'overflow-hidden' in _ticker_wrapper_tag(client)


# ── Ticker CSS animation ──────────────────────────────────────────────────────


class TestTickerAnimation:
    def test_keyframes_ticker_scroll_defined(self, client):
        assert '@keyframes ticker-scroll' in _style_block(client)

    def test_ticker_track_animation_property(self, client):
        style = _style_block(client)
        assert '.ticker-track' in style
        assert 'animation' in style

    def test_ticker_track_hover_pauses_animation(self, client):
        style = _style_block(client)
        assert 'animation-play-state: paused' in style

    def test_ticker_animation_infinite(self, client):
        assert 'infinite' in _style_block(client)

    def test_ticker_animation_linear(self, client):
        assert 'linear' in _style_block(client)

    def test_ticker_translate_x_keyframe(self, client):
        assert 'translateX' in _style_block(client)


# ── WhatsApp link unaffected ──────────────────────────────────────────────────


class TestWhatsAppUnaffected:
    def test_whatsapp_link_still_present(self, client):
        bar = _contact_bar_html(client)
        assert 'wa.me' in bar

    def test_whatsapp_number_displayed(self, client):
        assert '+91 9958808898' in _contact_bar_html(client)

    def test_whatsapp_icon_color(self, client):
        assert '#25D366' in _contact_bar_html(client)


# ── Contact bar layout ────────────────────────────────────────────────────────


class TestContactBarLayout:
    def test_bar_flex_justify_between(self, client):
        """Contact bar uses justify-between to spread Welcome (left), ticker (centre), WhatsApp (right)."""
        bar = _contact_bar_html(client)
        assert 'justify-between' in bar

    def test_bar_does_not_use_justify_end(self, client):
        """justify-end is the old layout; it must have been replaced by justify-between."""
        bar = _contact_bar_html(client)
        assert 'justify-end' not in bar

    def test_bar_has_gap(self, client):
        bar = _contact_bar_html(client)
        assert 'gap-4' in bar

    def test_three_elements_present(self, client):
        """Bar must have WhatsApp, ticker, and welcome — all three."""
        bar = _contact_bar_html(client)
        assert 'wa.me' in bar
        assert 'ticker-track' in bar
        assert 'Welcome to Styleus!' in bar

    def test_ticker_has_flex_1(self, client):
        """Ticker wrapper must carry flex-1 so it fills all available centre space."""
        wrapper = _ticker_wrapper_tag(client)
        assert 'flex-1' in wrapper

    def test_whatsapp_flex_shrink_zero(self, client):
        """WhatsApp anchor must not shrink so it stays pinned to the right."""
        bar = _contact_bar_html(client)
        whatsapp_pos = bar.index('wa.me')
        a_start = bar.rindex('<a ', 0, whatsapp_pos)
        a_end = bar.index('>', a_start) + 1
        anchor_tag = bar[a_start:a_end]
        assert 'flex-shrink-0' in anchor_tag

    def test_whatsapp_href(self, client):
        """WhatsApp link must point to the correct wa.me number."""
        bar = _contact_bar_html(client)
        assert 'wa.me/919958808898' in bar


# ── Consistency across pages ──────────────────────────────────────────────────


class TestContactBarConsistency:
    def test_welcome_on_products_page(self, client):
        assert 'Welcome to Styleus!' in _contact_bar_html(client, '/products')

    def test_welcome_on_services_page(self, client):
        assert 'Welcome to Styleus!' in _contact_bar_html(client, '/services')

    def test_welcome_on_login_page(self, client):
        assert 'Welcome to Styleus!' in _contact_bar_html(client, '/auth/login')

    def test_ticker_on_products_page(self, client):
        assert 'ticker-track' in _contact_bar_html(client, '/products')

    def test_ticker_on_services_page(self, client):
        assert 'ticker-track' in _contact_bar_html(client, '/services')

    def test_gold_color_on_all_pages(self, client):
        for path in ('/', '/products', '/services', '/auth/login'):
            assert '#FFD700' in _contact_bar_html(client, path), \
                f"Gold color missing on {path}"


# ── Smoke tests ────────────────────────────────────────────────────────────────


class TestSmokeTests:
    def test_homepage_200(self, client):
        assert client.get('/').status_code == 200

    def test_products_200(self, client):
        assert client.get('/products').status_code == 200

    def test_services_200(self, client):
        assert client.get('/services').status_code == 200

    def test_login_200(self, client):
        assert client.get('/auth/login').status_code == 200

    def test_register_200(self, client):
        assert client.get('/auth/register').status_code == 200

    def test_cart_redirects_or_200(self, client):
        code = client.get('/cart').status_code
        assert code in (200, 302, 308)

    def test_admin_redirects_when_unauthenticated(self, client):
        assert client.get('/admin/').status_code == 302
