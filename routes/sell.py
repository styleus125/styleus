import os
import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from werkzeug.utils import secure_filename

from models import db, UserListing

sell_bp = Blueprint('sell', __name__)


class ListingForm(FlaskForm):
    title = StringField('Item Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=2000)])
    asking_price = FloatField('Asking Price (₹)', validators=[Optional(), NumberRange(min=0)])
    condition = SelectField('Condition', choices=UserListing.CONDITION_CHOICES)
    image = FileField('Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    submit = SubmitField('Submit for Approval')


def save_listing_image(file):
    if file and file.filename:
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
    if form.validate_on_submit():
        image_url = save_listing_image(request.files.get('image')) or ''
        listing = UserListing(
            seller_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            asking_price=form.asking_price.data,
            condition=form.condition.data,
            image_url=image_url,
        )
        db.session.add(listing)
        db.session.commit()
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
    listings = UserListing.query.filter_by(status='approved')\
        .order_by(UserListing.created_at.desc()).all()
    return render_template('sell/listings.html', listings=listings, title='Used Items for Sale')
