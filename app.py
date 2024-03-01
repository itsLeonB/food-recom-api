import datetime
import os

import jwt
from bson import ObjectId
from bson.json_util import dumps
from flask import Flask, request
from pymongo import MongoClient

from User import User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'this is a secret'

client = MongoClient()
db = client["food-recom"]
users = db.users
restaurants = db.restaurants


def encode_jwt(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': str(user_id)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def decode_jwt(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.DecodeError as e:
        print(f"Error decoding JWT: {e}")
        return None


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = users.find_one({'email': email})
    if user and user['password'] == password:
        user = User(user_id=str(user['_id']), email=user['email'])
        token = encode_jwt(user.id)
        return {
            'message': 'Login successful',
            'token': token
        }
    else:
        return {'message': 'Login failed'}, 401


@app.route("/")
def index():
    token = request.headers.get('Authorization')
    if not token:
        return {'message': 'Token is missing'}, 401

    token = request.headers.get('Authorization').split()[1]
    user_id = decode_jwt(token.encode('utf-8'))

    if not user_id:
        return {'message': 'Invalid token'}, 401

    user = users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return {'message': 'User not found'}, 401

    return {'message': f'Hello, {user["email"]}!'}


@app.route("/restaurants")
def index_restaurants():
    data = dumps([restaurants.find({})])
    response = app.response_class(
        response=data,
        status=200,
        mimetype='application/json'
    )
    return response
