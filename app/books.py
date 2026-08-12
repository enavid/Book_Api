import logging
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.check_data import check_data, check_data_nl
from app.extensions import db
from app.models import Book, User

logger = logging.getLogger(__name__)
SORT_COLUMNS = {
    "book_id": Book.book_id,
    "rating": Book.rating,
    "published_year": Book.published_year,
    "book_name": Book.book_name,
}
def book_stats(books):
    books = list(books)
    ratings = [b.rating for b in books]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else None
    return {
        "total_books": len(books),
        "average_rating": avg,
        "distinct_genres": len({b.genre for b in books}),
    }
def resolve_sort(sort_key):
    return SORT_COLUMNS.get(sort_key, Book.book_id)
def pagination_meta(pagination):
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }
def is_owner(book_entry, username):
    return book_entry.get('added_by') == username
def error_response(message, status_code):
    return jsonify({'message': message}), status_code
dir_name = Path(__file__).resolve().parent.parent

books_bp = Blueprint('books', __name__)


@books_bp.route('/get_all_book', methods=['GET'])
@jwt_required()
def get_all_book():
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = max(request.args.get('per_page', 10, type=int), 0)

    query = db.select(Book)

    genre = request.args.get('genre')
    if genre:
        query = query.filter(Book.genre.ilike(genre))

    writer = request.args.get('writer')
    if writer:
        query = query.filter(Book.writer.ilike(writer))

    min_rating = request.args.get('min_rating', type=int)
    if min_rating is not None:
        query = query.filter(Book.rating >= min_rating)

    column = resolve_sort(request.args.get('sort'))
    if request.args.get('order') == 'desc':
        column = column.desc()
    query = query.order_by(column)

    pagination = db.paginate(query, page=page, per_page=per_page or 1, error_out=False)
    meta = pagination_meta(pagination)
    if per_page == 0:
        meta['per_page'] = 0
        return jsonify({'book': [], 'pagination': meta}), 200
    return jsonify({'book': [b.to_dict() for b in pagination.items], 'pagination': meta}), 200
@books_bp.route('/add_book', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    required = [
        ('book_name',str)
        ,('book_content',str)
        ,('book_id',int)
        ,('writer',str)
        ,('published_year',int)
        ,('rating',int)
        ,('genre',str),
        ('created_at',str)
    ]
    if check_data(data,required):
        pass
    elif not check_data(data,required):
        logger.warning(f'{get_jwt_identity()} sent invalid data to {request.path}')
        return error_response('data is bad!', 400)
    if data['rating'] < 0 or data['rating'] > 5:
        logger.warning(f"{get_jwt_identity} sent invalid data to {request.path}")
        return error_response('the rating is out of the range(0/5)',400)
    curent_year = datetime.today().year
    if data['published_year'] < 0 or data['published_year'] > curent_year:
        logger.warning(f"{get_jwt_identity()} sent invalid data to {request.path}")
        return error_response(f'the published_year is out of the range(0/{curent_year})',400)
    new_book = {
        'book_name': data['book_name'],
        'book_content': data['book_content'],
        'book_id': data['book_id'],
        'writer': data['writer'],
        'published_year': data['published_year'],
        'rating': data['rating'],
        'genre': data['genre'],
        'created_at': data['created_at'],
        'added_at': datetime.now().strftime('%Y-%m-%d'),
        'added_by': get_jwt_identity()
    }
    exists = db.session.get(Book, data['book_id'])
    if exists is not None:
        return error_response('book_id already exists!', 400)

    owner = db.session.scalar(db.select(User).filter_by(username=get_jwt_identity()))
    new_book = Book(
        book_id=data['book_id'], book_name=data['book_name'],
        book_content=data['book_content'], writer=data['writer'],
        published_year=data['published_year'], rating=data['rating'],
        genre=data['genre'], created_at=data['created_at'], owner=owner,
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'Success': 'New book added'}), 201
@books_bp.route('/delete_book/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book_row = db.session.get(Book, book_id)
    if book_row is None:
        return error_response('book_id not found!', 404)
    if book_row.owner.username != get_jwt_identity():
        return error_response('you are not authorized!', 403)
    db.session.delete(book_row)
    db.session.commit()
    return jsonify({'Success': 'Book deleted'}), 200


@books_bp.route('/search', methods=['POST'])
@jwt_required()
def search():
    data = request.get_json()
    required = [('book_name',str),('genre',str),('writer',str)]
    if check_data_nl(data,required):
        pass
    elif not check_data_nl(data,required):
        return error_response('At least one search field is required', 400)
    conditions = []
    if 'book_name' in data:
        conditions.append(Book.book_name.ilike(f"%{data['book_name']}%"))
    if 'genre' in data:
        conditions.append(Book.genre.ilike(f"%{data['genre']}%"))
    if 'writer' in data:
        conditions.append(Book.writer.ilike(f"%{data['writer']}%"))
    results = db.session.scalars(db.select(Book).filter(db.or_(*conditions))).all()
    return jsonify([b.to_dict() for b in results]), 200
@books_bp.route('/update_book/<int:book_id>', methods=['POST'])
@jwt_required()
def update_book(book_id):
    data = request.get_json()
    required = [
        ('book_name', str)
        , ('book_content', str)
        , ('book_id', int)
        , ('writer', str)
        , ('rating', int)
        , ('genre', str),
        ('created_at', str)
    ]
    if not check_data(data, required):
        logger.warning(f'{get_jwt_identity()} sent invalid data to {request.path}')
        return error_response('The data content not has all the required fields!', 400)

    exists = db.session.get(Book, book_id)
    if exists is None:
        return error_response('book_id not found!', 404)
    book_row = db.session.get(Book, book_id)
    if  book_row.owner.username != get_jwt_identity():
        return error_response('you are not authorized!', 403)
    if data['rating'] < 0 or data['rating'] > 5:
        logger.warning(f"{get_jwt_identity()} sent invalid data to {request.path}")
        return error_response('the rating is out of the range(0/5)', 400)
    curent_year = datetime.today().year
    if data['published_year'] < 0 or data['published_year'] > curent_year:
        logger.warning(f"{get_jwt_identity()} sent invalid data to {request.path}")
        return error_response(f'the published_year is out of the range(0/{curent_year})', 400)

    book_row.book_name = data['book_name']
    book_row.book_content = data['book_content']
    book_row.book_id = data['book_id']
    book_row.writer = data['writer']
    book_row.rating = data['rating']
    book_row.genre = data['genre']
    book_row.created_at = data['created_at']
    book_row.published_year = curent_year
    db.session.add(book_row)
    db.session.commit()

    logger.info(f'{get_jwt_identity()} updated book {data['book_id']}')
    return jsonify({'Success': 'Book updated'}), 200
@books_bp.route('/get_book/<int:book_id>', methods=['get'])
@jwt_required()
def get_book(book_id):
    book_row = db.session.get(Book, book_id)
    if book_row is None:
        return error_response('book_id not found!', 404)
    return jsonify(book_row.to_dict()), 200
@books_bp.route('/my_books', methods=['GET'])
@jwt_required()
def my_books():
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = max(request.args.get('per_page', 10, type=int), 0)

    query = (
        db.select(Book)
        .join(User, Book.owner_id == User.id)
        .filter(User.username == get_jwt_identity())
        .order_by(Book.book_id)
    )
    pagination = db.paginate(query, page=page, per_page=per_page or 1, error_out=False)
    meta = pagination_meta(pagination)

    if per_page == 0:
        meta['per_page'] = 0
        return jsonify({'book': [], 'pagination': meta}), 200
    return jsonify({'book': [b.to_dict() for b in pagination.items], 'pagination': meta}), 200
@books_bp.route('/genres', methods=['GET'])
@jwt_required()
def genres():
    rows = db.session.scalars(
        db.select(Book.genre).distinct().order_by(Book.genre)
    ).all()
    return jsonify({'genres': rows}), 200
@books_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    user = db.session.scalar(db.select(User).filter_by(username=get_jwt_identity()))
    if user is None:
        return error_response('user not found', 404)
    return jsonify(book_stats(user.books)), 200
