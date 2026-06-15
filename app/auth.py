from flask import Blueprint, request, jsonify
import os
import bcrypt
import json
from check_data import check_data
import logging
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required,get_jwt_identity
import datetime
from pathlib import Path

file = Path(__file__).resolve()
dir_name = file.parent.parent


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
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
        return jsonify({'message': 'data is bad'}), 400
    if len(data['username']) < 8:
        return jsonify({'message': 'username is too short'}),400
    if '\\' in data['username'] or '\'' in data['username']:
        return jsonify({'message': 'username cannot write \\,\''}),400
    if not isinstance(data['password'], str):
        return jsonify({'message': 'password is not string'}),400
    if not isinstance(data['username'], str):

        return jsonify({'message': 'username is not string'}),400
    data['password'] = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    file_name = os.path.join(os.path.join(dir_name,os.path.join('data','Users')),data['username'])+'.json'
    if os.path.exists(file_name):
        return jsonify({'message': 'Username already exists'}), 409
    with open(file_name, 'w') as f:
        f.write(json.dumps(data))
    return jsonify({'message': 'success'})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data is None or 'password' not in data or 'username' not in data:
        return jsonify({'message': 'not have all'}), 400
    plain = data['password'].encode('utf-8')
    try:
        file_name = os.path.join(os.path.join(dir_name, os.path.join('data','Users')), data['username']) + '.json'
        with open(file_name, 'r') as f:
            json_data = json.loads(f.read())
            stored = json_data['password'].encode('utf-8')
            if bcrypt.checkpw(plain, stored) and json_data['username'] == data['username']:
                token = make_token(json_data['username'])
                refresh_token = make_refresh_token(json_data['username'])
                logger.info(f'{data['username']} loged!')
                return jsonify({'message': 'success', 'token': token, 'refresh_token': refresh_token}), 200
            elif not bcrypt.checkpw(plain, stored) or json_data['username'] != data['username']:
                logger.warning(f'{data['username']} not loged!')
                return jsonify({'message': 'Username or Password is bad'}), 400
    except FileNotFoundError:
        return jsonify({'message': 'Username or Password is bad'}), 400
@auth_bp.route('/refresh_token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    username = get_jwt_identity()
    new_token = make_token(username)
    return jsonify({'token': new_token}), 200