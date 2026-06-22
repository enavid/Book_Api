from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json
import check_data
from flask_jwt_extended import jwt_required, get_jwt_identity
from pathlib import Path

def is_owner(book_entry, username):
    return book_entry.get('added_by') == username
def error_response(message, status_code):
    return jsonify({'message': message}), status_code
dir_name = Path(__file__).resolve().parent.parent
BOOKS_FILE = os.path.join(dir_name, 'data', 'Book_Loader.json')

def load_books() -> dict:
    with open(BOOKS_FILE) as f:
        return json.load(f)

def save_books(books: dict) -> None:
    tmp_path = BOOKS_FILE + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(books, f)
    os.replace(tmp_path, BOOKS_FILE)

books_bp = Blueprint('books', __name__)
book = load_books()

@books_bp.route('/get_all_book', methods=['GET'])
@jwt_required()
def get_all_book():
    book2 = list(book.values())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = book2[start:end]
    return jsonify({'book': paginated}), 200
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
    if check_data.check_data(data,required):
        pass
    elif not check_data.check_data(data,required):
        return error_response('data is bad!', 400)
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
    if str(new_book['book_id']) in book:
        return error_response('book_id already exists!', 400)
    book[str(new_book['book_id'])] = new_book
    save_books(book)
    return jsonify({'Success': 'New book added'}), 201
@books_bp.route('/delete_book/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    if not is_owner(book[str(book_id)],get_jwt_identity()):
        return error_response('you are not authorized!', 401)
    deleted_book = None
    for i in book.values():
        if i["book_id"] == book_id:
            deleted_book = str(i['book_id'])
            break
    if deleted_book == None:
        return error_response('book_id not found!', 404)
    del book[int(deleted_book)]
    save_books(book)
    return jsonify({'Success': 'Book deleted'}), 200
@books_bp.route('/search', methods=['POST'])
@jwt_required()
def search():
    data = request.get_json()
    show = []
    required = [('book_name',str),('genre',str),('writer',str)]
    if check_data.check_data_nl(data,required):
        pass
    elif not check_data.check_data_nl(data,required):
        return error_response('At least one search field is required', 400)
    if 'book_name' in data:
        for i in book.values():
            if data['book_name'].lower() in i['book_name'].lower():
                show.append(i)
    elif 'genre' in data:
        for i in book.values():
            if data['genre'].lower() in i['genre'].lower():
                show.append(i)
    elif 'writer' in data:
        for i in book.values():
            if data['writer'].lower() in i['writer'].lower():
                show.append(i)
    return jsonify(show), 200
@books_bp.route('/update_book/<int:book_id>', methods=['POST'])
@jwt_required()
def update_book(book_id):
    data = request.get_json()
    required = [
        ('book_name', str)
        , ('book_content', str)
        , ('book_id', int)
        , ('writer', str)
        , ('published_year', int)
        , ('rating', int)
        , ('genre', str),
        ('created_at', str)
    ]
    if check_data.check_data(data,required):
        pass
    elif not check_data.check_data(data,required):
        return error_response('The data content not has all the required fields!', 400)
    new_book = None
    for i in book.values():
        if i['book_id'] == book_id and is_owner(i,get_jwt_identity()):
            i['book_name'] = data['book_name']
            i['book_content'] = data['book_content']
            i['book_id'] = book_id
            i['writer'] = data['writer']
            i['published_year'] = data['published_year']
            i['rating'] = data['rating']
            i['genre'] = data['genre']
            i['created_at'] = data['created_at']
            i['added_at'] = datetime.now().strftime('%Y-%m-%d')
            i['added_by'] = get_jwt_identity()
            new_book = i
    if new_book is None:
        return error_response('book_id not found!', 404)
    book[new_book['book_id']] = new_book
    save_books(book)
    return jsonify({'Success': 'Book updated'}), 200
@books_bp.route('/get_book/<int:book_id>', methods=['get'])
@jwt_required()
def get_book(book_id):
    for i in book.values():
        if i['book_id'] == book_id:
            return jsonify(i), 200
    return error_response('book_id not found!', 404)