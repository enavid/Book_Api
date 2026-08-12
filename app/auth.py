import datetime
import logging
import re
from pathlib import Path

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app.check_data import check_data
from app.extensions import db
from app.models import User


def error_response(message, status_code):
    return jsonify({'message': message}), status_code

file = Path(__file__).resolve()
dir_name = file.parent.parent


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

def make_token(identity):
    return create_access_token(identity=identity,expires_delta=datetime.timedelta(hours=1))
def make_refresh_token(identity):
    return create_refresh_token(identity=identity,expires_delta=datetime.timedelta(days=30))

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required = [('username',str), ('password',str)]
    if check_data(data, required):
        pass
    elif not check_data(data, required):
        return error_response('data is none',400)
    if len(data['username']) < 8:
        return error_response('username is too short',400)
    if not re.match(r'^[a-zA-Z0-9_]+$', data['username']):
        return error_response('Username can only contain letters, numbers, and underscores',400)
    if not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
        return error_response('username and password must be strings', 400)
    existing = db.session.scalar(db.select(User).filter_by(username=data['username']))
    if existing is not None:
        return error_response('username already exists', 409)
    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    user = User(username=data['username'].strip(), password=hashed)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'success'})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    required = [('username', str), ('password', str)]
    if not check_data(data, required):
        return error_response('data is bad!', 400)
    user = db.session.scalar(db.select(User).filter_by(username=data['username'].strip()))
    required = [('username', str), ('password', str)]
    if user is None:
        return error_response('username and password do not match', 400)

    plain = data['password'].encode('utf-8')
    if bcrypt.checkpw(plain, user.password.encode('utf-8')):
        token = make_token(user.username)
        refresh_token = make_refresh_token(user.username)
        logger.info(f"{user.username} loged!")
        return jsonify({'message': 'success', 'token': token, 'refresh_token': refresh_token}), 200
    return error_response('username and password do not match', 400)

@auth_bp.route('/refresh_token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    username = get_jwt_identity()
    new_token = make_token(username)
    return jsonify({'token': new_token}), 200
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = db.session.scalar(db.select(User).filter_by(username=get_jwt_identity()))
    if user is None:
        return error_response('user not found', 404)
    return jsonify(user.summary()), 200
@auth_bp.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json()
    required = [('old_password', str), ('new_password', str)]
    if not check_data(data, required):
        return error_response('data is bad!', 400)

    user = db.session.scalar(db.select(User).filter_by(username=get_jwt_identity()))
    if user is None:
        return error_response('user not found', 404)

    if not bcrypt.checkpw(data['old_password'].encode('utf-8'), user.password.encode('utf-8')):
        return error_response('old password is incorrect', 403)

    user.password = bcrypt.hashpw(
        data['new_password'].encode('utf-8'), bcrypt.gensalt(12)
    ).decode('utf-8')
    db.session.commit()
    return jsonify({'message': 'success'}), 200
