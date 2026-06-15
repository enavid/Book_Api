from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json
from check_data import check_data,check_data_nl
from flask_jwt_extended import jwt_required, get_jwt_identity
from pathlib import Path

file = Path(__file__).resolve()
dir_name = file.parent.parent
books_bp = Blueprint('books', __name__)
print(dir_name)
with open(os.path.join(os.path.join(dir_name,'data'),'Book_Loader.json')) as f:
    data = json.load(f)
    book = data

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
    if check_data(data,required):
        pass
    elif not check_data_nl(data,required):
        return jsonify({'message': 'Data is bad!'}), 400
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
        return jsonify({'message': 'edit book_id!'}), 400
    book[new_book['book_id']] = new_book
    with open(os.path.join(os.path.join(dir_name,"data"),"Book_Loader.json"), 'w') as f:
        f.write(json.dumps(book))
    return jsonify({'Success': 'New book added'}), 201
@books_bp.route('/delete_book/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    if not get_jwt_identity() == book[book_id]['added_by']:
        return jsonify({'message': 'You can\'t delete it!'}), 404
    deleted_book = None
    for i in book.values():
        if i["book_id"] == book_id:
            deleted_book = str(i['book_id'])
            break
    if deleted_book == None:
        return jsonify({'error': 'Not found!'}), 404
    del book[int(deleted_book)]
    with open(os.path.join(os.path.join(dir_name,"data"),'Book_Loader.json'), 'w') as f:
        f.write(json.dumps(book))
    return jsonify({'Success': 'Book deleted'}), 200
@books_bp.route('/search', methods=['POST'])
@jwt_required()
def search():
    data = request.get_query()
    show = []
    required = [('book_name',str),('genre',str),('writer',str)]
    if check_data_nl(data,required):
        pass
    elif not check_data_nl(data,required):
        return jsonify({'message': 'Data is bad!'}), 400
    if 'book_name' not in data and 'genre' not in data or 'writer' not in data:
        return jsonify({'Data is none'}), 400
    if 'book_name' in data:
        for i in book.values():
            if i['book_name'].lower() in data['book_name'].lower():
                show.append(i)
    elif 'genre' in data:
        for i in book.values():
            if i['genre'].lower() in data['genre'].lower():
                show.append(i)
    elif 'writer' in data:
        for i in book.values():
            if i['writer'].lower() in data['writer'].lower():
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
    if check_data(data,required):
        pass
    elif not check_data(data,required):
        return jsonify({'message': 'Data is bad!'}), 400
    for i in book.values():
        if i['book_id'] == book_id and get_jwt_identity() == i['added_by']:
            i['book_name'] = data['book_name']
            i['book_content'] = data['book_content']
            i['book_id'] = book_id
            i['writer'] = data['writer']
            i['published_year'] = data['published_year']
            i['rating'] = data['rating']
            i['genre'] = data['genre']
            i['created_at'] = data['created_at']
            i['added_at'] = datetime.now().strftime('%Y-%m-%d')
            i['added_by'] = request.headers.get('Authorization')
            new_book = i
    if new_book is None:
        return jsonify({'message': 'Not found!'}), 404
    book[new_book['book_id']] = new_book
    with open(os.path.join(os.path.join(dir_name,'data'),'Book_Loader.json'),'w') as f:
        f.write(json.dumps(book))
    return jsonify({'Success': 'Book updated'}), 200
@books_bp.route('/get_book/<int:book_id>', methods=['get'])
@jwt_required()
def get_book(book_id):
    for i in book.values():
        if i['book_id'] == book_id:
            return jsonify(i), 200
    return jsonify({'message': 'Not found!'}), 404