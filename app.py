from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey123'
app.config['JWT_SECRET_KEY'] = 'jwtsecretkey456'
jwt = JWTManager(app)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Update with your MongoDB URI
db = client['map_project']
users_collection = db['users']
landmarks_collection = db['landmarks']
routes_collection = db['routes']

# Admin users
ADMINS = ["shrihari@example.com", "alexjmathew@example.com"]

# Middleware to check user role
def check_role():
    if 'user' not in session:
        return None
    email = session['user']
    return 'admin' if email in ADMINS else 'user'

@app.route('/')
def index():
    role = check_role()
    return render_template('index.html', role=role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user'] = email
            access_token = create_access_token(identity=email)
            return jsonify({'token': access_token, 'redirect': url_for('index')}), 200
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({'email': email, 'password': hashed, 'created_at': datetime.utcnow()})
    return jsonify({'message': 'User created', 'redirect': url_for('login')}), 201

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if check_role() != 'admin':
        return redirect(url_for('index'))
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])
    return render_template('admin.html', users=users)

@app.route('/api/landmarks', methods=['GET', 'POST'])
@jwt_required()
def landmarks():
    role = check_role()
    if not role:
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'POST':
        data = request.json
        landmark = {
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'lat': data['lat'],
            'lng': data['lng'],
            'description': data['description'],
            'owner': get_jwt_identity(),
            'created_at': datetime.utcnow()
        }
        landmarks_collection.insert_one(landmark)
        landmark['_id'] = str(landmark['_id'])
        return jsonify(landmark)
    
    query = {} if role == 'admin' else {'owner': get_jwt_identity()}
    landmarks = list(landmarks_collection.find(query))
    for lm in landmarks:
        lm['_id'] = str(lm['_id'])
    return jsonify(landmarks)

@app.route('/api/landmarks/<id>', methods=['PUT', 'DELETE'])
@jwt_required()
def modify_landmark(id):
    role = check_role()
    if not role:
        return jsonify({"error": "Unauthorized"}), 401
    
    landmark = landmarks_collection.find_one({'id': id})
    if not landmark or (role != 'admin' and landmark['owner'] != get_jwt_identity()):
        return jsonify({"error": "Forbidden"}), 403
    
    if request.method == 'PUT':
        data = request.json
        update_data = {
            'name': data.get('name', landmark['name']),
            'description': data.get('description', landmark['description']),
            'lat': data.get('lat', landmark['lat']),
            'lng': data.get('lng', landmark['lng'])
        }
        landmarks_collection.update_one({'id': id}, {'$set': update_data})
        return jsonify(update_data)
    
    if request.method == 'DELETE':
        landmarks_collection.delete_one({'id': id})
        return jsonify({"message": "Deleted"})

@app.route('/api/routes', methods=['GET', 'POST'])
@jwt_required()
def routes():
    role = check_role()
    if not role:
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'POST':
        data = request.json
        route = {
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'path': data['path'],
            'owner': get_jwt_identity(),
            'created_at': datetime.utcnow()
        }
        routes_collection.insert_one(route)
        route['_id'] = str(route['_id'])
        return jsonify(route)
    
    query = {} if role == 'admin' else {'owner': get_jwt_identity()}
    routes = list(routes_collection.find(query))
    for rt in routes:
        rt['_id'] = str(rt['_id'])
    return jsonify(routes)

if __name__ == '__main__':
    app.run(debug=True)
