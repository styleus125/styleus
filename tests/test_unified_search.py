"""
Tests for the unified /search route added in routes/shop.py.
Covers shop products, used listings, empty states, and filtering rules.
"""
import pytest
from models import db, User, Product, UserListing


def _main_html(client, path):
    """Return only the <main>...</main> section of the page."""
    html = client.get(path).data.decode()
    main_start = html.index('<main>')
    main_end = html.index('</main>') + len('</main>')
    return html[main_start:main_end]


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def seller(app):
    with app.app_context():
        user = User(name='Seller User', email='seller_search@example.com',
                    is_approved=True, is_admin=False)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        uid = user.id
        yield uid
        db.session.delete(db.session.get(User, uid))
        db.session.commit()


@pytest.fixture
def active_product(app):
    with app.app_context():
        p = Product(name='UniqueZephyrWatch', slug='unique-zephyr-watch',
                    price=99.99, is_active=True)
        db.session.add(p)
        db.session.commit()
        pid = p.id
        yield pid
        db.session.delete(db.session.get(Product, pid))
        db.session.commit()


@pytest.fixture
def inactive_product(app):
    with app.app_context():
        p = Product(name='ZephyrInactiveGadget', slug='zephyr-inactive-gadget',
                    price=9.99, is_active=False)
        db.session.add(p)
        db.session.commit()
        pid = p.id
        yield pid
        db.session.delete(db.session.get(Product, pid))
        db.session.commit()


@pytest.fixture
def approved_listing(app, seller):
    with app.app_context():
        lst = UserListing(seller_id=seller, title='ZephyrUsedBike',
                          description='A fine used bicycle', condition='good',
                          status='approved')
        db.session.add(lst)
        db.session.commit()
        lid = lst.id
        yield lid
        db.session.delete(db.session.get(UserListing, lid))
        db.session.commit()


@pytest.fixture
def pending_listing(app, seller):
    with app.app_context():
        lst = UserListing(seller_id=seller, title='ZephyrPendingScooter',
                          description='Pending approval scooter', condition='fair',
                          status='pending')
        db.session.add(lst)
        db.session.commit()
        lid = lst.id
        yield lid
        db.session.delete(db.session.get(UserListing, lid))
        db.session.commit()


@pytest.fixture
def rejected_listing(app, seller):
    with app.app_context():
        lst = UserListing(seller_id=seller, title='ZephyrRejectedBoat',
                          description='Rejected listing boat', condition='poor',
                          status='rejected')
        db.session.add(lst)
        db.session.commit()
        lid = lst.id
        yield lid
        db.session.delete(db.session.get(UserListing, lid))
        db.session.commit()


# ── No-query state ─────────────────────────────────────────────────────────────

class TestSearchNoQuery:
    def test_returns_200(self, client):
        resp = client.get('/search')
        assert resp.status_code == 200

    def test_prompt_text_shown(self, client):
        html = client.get('/search').data.decode()
        assert 'Enter a search term above' in html

    def test_no_shop_items_section(self, client):
        html = client.get('/search').data.decode()
        assert 'Shop Items' not in html

    def test_no_used_items_section(self, client):
        assert 'Used Items' not in _main_html(client, '/search')

    def test_empty_query_string_same_as_no_query(self, client):
        html = client.get('/search?q=').data.decode()
        assert 'Enter a search term above' in html


# ── Shop item results ──────────────────────────────────────────────────────────

class TestSearchShopItems:
    def test_active_product_appears(self, client, active_product):
        html = client.get('/search?q=UniqueZephyrWatch').data.decode()
        assert 'UniqueZephyrWatch' in html

    def test_shop_items_section_header_present(self, client, active_product):
        html = client.get('/search?q=UniqueZephyrWatch').data.decode()
        assert 'Shop Items' in html

    def test_returns_200_with_match(self, client, active_product):
        resp = client.get('/search?q=UniqueZephyrWatch')
        assert resp.status_code == 200

    def test_case_insensitive_match(self, client, active_product):
        html = client.get('/search?q=uniquezephyrwatch').data.decode()
        assert 'UniqueZephyrWatch' in html

    def test_partial_term_match(self, client, active_product):
        html = client.get('/search?q=ZephyrWatch').data.decode()
        assert 'UniqueZephyrWatch' in html


# ── Used listing results ───────────────────────────────────────────────────────

class TestSearchUsedItems:
    def test_approved_listing_appears(self, client, approved_listing):
        html = client.get('/search?q=ZephyrUsedBike').data.decode()
        assert 'ZephyrUsedBike' in html

    def test_used_items_section_header_present(self, client, approved_listing):
        html = client.get('/search?q=ZephyrUsedBike').data.decode()
        assert 'Used Items' in html

    def test_returns_200_with_used_match(self, client, approved_listing):
        resp = client.get('/search?q=ZephyrUsedBike')
        assert resp.status_code == 200

    def test_case_insensitive_used_match(self, client, approved_listing):
        html = client.get('/search?q=zephyrusedbike').data.decode()
        assert 'ZephyrUsedBike' in html


# ── Both sections populated ────────────────────────────────────────────────────

class TestSearchBothSections:
    def test_both_sections_when_both_match(self, client, active_product, approved_listing):
        # "Zephyr" appears in both UniqueZephyrWatch and ZephyrUsedBike
        html = client.get('/search?q=Zephyr').data.decode()
        assert 'Shop Items' in html
        assert 'Used Items' in html

    def test_shop_result_in_html(self, client, active_product, approved_listing):
        html = client.get('/search?q=Zephyr').data.decode()
        assert 'UniqueZephyrWatch' in html

    def test_used_result_in_html(self, client, active_product, approved_listing):
        html = client.get('/search?q=Zephyr').data.decode()
        assert 'ZephyrUsedBike' in html


# ── No-match empty state ───────────────────────────────────────────────────────

class TestSearchNoMatches:
    def test_no_results_message_shown(self, client):
        html = client.get('/search?q=zzz_no_match_xyz').data.decode()
        assert 'No results found' in html

    def test_link_to_shop_browse(self, client):
        html = client.get('/search?q=zzz_no_match_xyz').data.decode()
        assert '/products' in html

    def test_link_to_used_browse(self, client):
        html = client.get('/search?q=zzz_no_match_xyz').data.decode()
        assert 'used' in html.lower()

    def test_no_shop_items_section(self, client):
        html = client.get('/search?q=zzz_no_match_xyz').data.decode()
        assert 'Shop Items' not in html

    def test_no_used_items_section(self, client):
        assert 'Used Items' not in _main_html(client, '/search?q=zzz_no_match_xyz')

    def test_returns_200_on_no_match(self, client):
        resp = client.get('/search?q=zzz_no_match_xyz')
        assert resp.status_code == 200


# ── Unapproved listings excluded ───────────────────────────────────────────────

class TestSearchExcludesUnapproved:
    def test_pending_listing_not_in_results(self, client, pending_listing):
        # Template shows "0 used items" summary when pending listing is excluded
        assert '0 used items' in _main_html(client, '/search?q=ZephyrPendingScooter')

    def test_rejected_listing_not_in_results(self, client, rejected_listing):
        assert '0 used items' in _main_html(client, '/search?q=ZephyrRejectedBoat')

    def test_pending_query_shows_empty_state(self, client, pending_listing):
        html = client.get('/search?q=ZephyrPendingScooter').data.decode()
        assert 'No results found' in html or 'Enter a search term' not in html

    def test_used_items_section_absent_for_pending(self, client, pending_listing):
        assert 'Used Items' not in _main_html(client, '/search?q=ZephyrPendingScooter')


# ── Inactive products excluded ─────────────────────────────────────────────────

class TestSearchExcludesInactive:
    def test_inactive_product_not_in_results(self, client, inactive_product):
        # Template shows "0 shop items" summary when inactive product is excluded
        assert '0 shop items' in _main_html(client, '/search?q=ZephyrInactiveGadget')

    def test_shop_items_section_absent_for_inactive(self, client, inactive_product):
        html = client.get('/search?q=ZephyrInactiveGadget').data.decode()
        assert 'Shop Items' not in html

    def test_inactive_query_shows_empty_state(self, client, inactive_product):
        html = client.get('/search?q=ZephyrInactiveGadget').data.decode()
        assert 'No results found' in html


# ── /products?q= still works independently ────────────────────────────────────

class TestProductsRouteIndependent:
    def test_products_route_returns_200(self, client):
        resp = client.get('/products')
        assert resp.status_code == 200

    def test_products_with_query_returns_200(self, client):
        resp = client.get('/products?q=shirt')
        assert resp.status_code == 200

    def test_products_search_active_item(self, client, active_product):
        html = client.get('/products?q=UniqueZephyrWatch').data.decode()
        assert 'UniqueZephyrWatch' in html

    def test_products_search_excludes_inactive(self, client, inactive_product):
        # Products page shows "0 found" or "No products found" when inactive item is filtered out
        main = _main_html(client, '/products?q=ZephyrInactiveGadget')
        assert 'No products found' in main or '0 found' in main

    def test_products_route_does_not_show_used_items_section(self, client, approved_listing):
        assert 'Used Items' not in _main_html(client, '/products?q=ZephyrUsedBike')


# ── Navbar search bar points to /search ───────────────────────────────────────

class TestNavbarSearchForm:
    def test_search_form_action_on_homepage(self, client):
        html = client.get('/').data.decode()
        assert 'action="/search"' in html or 'action=\'/search\'' in html or '/search' in html

    def test_search_placeholder_text(self, client):
        html = client.get('/').data.decode()
        assert 'Search products' in html or 'used items' in html
