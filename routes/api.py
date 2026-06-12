import os
import re
import uuid
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from slugify import slugify
from werkzeug.utils import secure_filename

from models import db, BlogPost, ChatConfig, ChatFAQ, ChatSession, ChatMessage

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


@api_bp.route('/chat/message', methods=['POST'])
def chat_message():
    data = request.get_json() or {}
    user_text = (data.get('message') or '').strip()
    session_id = (data.get('session_id') or '').strip()

    if not user_text:
        return jsonify({'error': 'No message provided'}), 400

    config = ChatConfig.query.first()
    if not config or not config.enabled:
        return jsonify({'error': 'Chat is disabled'}), 403

    chat_session = None
    if session_id:
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        session_id = uuid.uuid4().hex
        chat_session = ChatSession(session_id=session_id)
        db.session.add(chat_session)
        db.session.flush()

    db.session.add(ChatMessage(session_id=chat_session.id, role='user', content=user_text))

    reply = _faq_match(user_text) or config.fallback_message

    db.session.add(ChatMessage(session_id=chat_session.id, role='assistant', content=reply))
    chat_session.last_message_at = datetime.utcnow()
    chat_session.message_count = (chat_session.message_count or 0) + 2
    db.session.commit()

    return jsonify({'reply': reply, 'session_id': session_id})


def _faq_match(text):
    faqs = ChatFAQ.query.filter_by(enabled=True).order_by(ChatFAQ.sort_order).all()
    lower = text.lower()
    best, top = None, 0
    for faq in faqs:
        score = 0
        if faq.keywords:
            for kw in [k.strip().lower() for k in faq.keywords.split(',') if k.strip()]:
                if kw and kw in lower:
                    score += 2
        for word in re.findall(r'\w+', faq.question.lower()):
            if len(word) > 2 and word in lower:
                score += 1
        if score > top:
            top, best = score, faq
    return best.answer if best and top > 0 else None
