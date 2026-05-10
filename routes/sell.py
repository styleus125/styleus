import os
import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField, TelField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email
from werkzeug.utils import secure_filename

from models import db, UserListing, SellCategory
from telegram import send_telegram

sell_bp = Blueprint('sell', __name__)


class ListingForm(FlaskForm):
    seller_name  = StringField('Your Name',  validators=[DataRequired(), Length(max=120)])
    seller_email = StringField('Your Email', validators=[DataRequired(), Email(), Length(max=200)])
    seller_phone = StringField('Your Phone', validators=[DataRequired(), Length(min=10, max=20)])
    title = StringField('Item Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    sell_category_id = SelectField('Category', coerce=int, validators=[Optional()])
    asking_price = FloatField('Asking Price (₹)', validators=[Optional(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=UserListing.CONDITION_CHOICES)
    image = FileField('Photo 1', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    image2 = FileField('Photo 2', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    image3 = FileField('Photo 3', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    image4 = FileField('Photo 4', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    submit = SubmitField('Submit for Approval')


def save_listing_image(file):
    if file and file.filename:
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > current_app.config['MAX_IMAGE_SIZE']:
            raise ValueError(f'"{file.filename}" is {size // (1024*1024) or "<1"} MB — maximum allowed is 2 MB.')
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique = f"listing_{name}_{int(time.time())}{ext}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique)
        file.save(path)
        return f'/static/uploads/{unique}'
    return None


@sell_bp.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_form():
    form = ListingForm()
    sell_cats = SellCategory.query.filter_by(is_active=True).order_by(SellCategory.sort_order, SellCategory.name).all()
    form.sell_category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in sell_cats]
    if form.validate_on_submit():
        try:
            image_url  = save_listing_image(request.files.get('image'))  or ''
            image_url2 = save_listing_image(request.files.get('image2')) or ''
            image_url3 = save_listing_image(request.files.get('image3')) or ''
            image_url4 = save_listing_image(request.files.get('image4')) or ''
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('sell/sell_form.html', form=form, title='Sell Your Item')
        listing = UserListing(
            seller_id=current_user.id,
            seller_name=form.seller_name.data,
            seller_email=form.seller_email.data,
            seller_phone=form.seller_phone.data,
            sell_category_id=form.sell_category_id.data or None,
            title=form.title.data,
            description=form.description.data,
            asking_price=form.asking_price.data,
            condition=form.condition.data,
            image_url=image_url,
            image_url_2=image_url2,
            image_url_3=image_url3,
            image_url_4=image_url4,
        )
        db.session.add(listing)
        db.session.commit()
        price_str = f"₹{listing.asking_price:,.0f}" if listing.asking_price else "Not set"
        send_telegram(
            f"🛍️ <b>New Sell Listing</b>\n"
            f"Item: {listing.title}\n"
            f"Condition: {listing.condition}\n"
            f"Price: {price_str}\n"
            f"Seller: {listing.seller_name} ({listing.seller_phone})\n"
            f"⏳ Pending admin approval"
        )
        flash('Your listing has been submitted and is pending admin approval.', 'success')
        return redirect(url_for('sell.my_listings'))
    return render_template('sell/sell_form.html', form=form, title='Sell Your Item')


@sell_bp.route('/sell/my-listings')
@login_required
def my_listings():
    listings = UserListing.query.filter_by(seller_id=current_user.id)\
        .order_by(UserListing.created_at.desc()).all()
    return render_template('sell/my_listings.html', listings=listings, title='My Listings')


@sell_bp.route('/sell/listings')
def public_listings():
    listings = UserListing.query.filter_by(status='approved', is_active=True)\
        .order_by(UserListing.created_at.desc()).all()
    return render_template('sell/listings.html', listings=listings, title='Used Items for Sale')
