import os
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from slugify import slugify
from werkzeug.utils import secure_filename

from models import db, BlogPost

api_bp = Blueprint('api', __name__)


@api_bp.route('/blog/draft', methods=['POST'])
def blog_draft():
    token = request.headers.get('X-API-Token', '')
    expected = current_app.config.get('BLOG_API_TOKEN', '')
    if not token or not expected or token != expected:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    title = (data.get('title') or '').strip()
    excerpt = (data.get('excerpt') or '').strip()
    body = (data.get('body') or '').strip()
    cover_image_url = (data.get('cover_image_url') or '').strip()

    if not title:
        return jsonify({'error': 'title is required'}), 400
    if not excerpt:
        return jsonify({'error': 'excerpt is required'}), 400
    if not body:
        return jsonify({'error': 'body is required'}), 400

    slug = slugify(title)
    base_slug = slug
    counter = 1
    while BlogPost.query.filter_by(slug=slug).first():
        slug = f'{base_slug}-{counter}'
        counter += 1

    post = BlogPost(
        title=title,
        slug=slug,
        excerpt=excerpt,
        body=body,
        cover_image_url=cover_image_url,
        is_published=False
    )
    db.session.add(post)
    db.session.commit()

    return jsonify({
        'success': True,
        'id': post.id,
        'slug': post.slug,
        'admin_url': f'/admin/blog/{post.id}/edit'
    }), 201


@api_bp.route('/upload-image', methods=['POST'])
def upload_image():
    token = request.headers.get('X-API-Token', '')
    expected = current_app.config.get('BLOG_API_TOKEN', '')
    if not token or not expected or token != expected:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    f = request.files['file']
    ext = os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.webp', '.mp4'}:
        return jsonify({'error': 'Invalid file type'}), 400

    prefix = 'media' if ext == '.mp4' else 'blog'
    filename = f'{prefix}_{uuid.uuid4().hex}{ext}'
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    f.save(save_path)

    url = f'/static/uploads/{filename}'
    return jsonify({'success': True, 'url': url}), 201
