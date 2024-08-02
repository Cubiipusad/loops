from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loops.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    wallet = db.relationship('Wallet', backref='owner', uselist=False)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    balance = db.Column(db.Float, default=0)
    last_earning_date = db.Column(db.DateTime, default=datetime.utcnow)

class Loop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    production_rate = db.Column(db.Float, nullable=False)
    substance = db.Column(db.String(50), nullable=False)
    produces = db.Column(db.String(50), nullable=False)  # Type of loop this plant produces

# Create tables
with app.app_context():
    db.create_all()

# Define Loop Types
loop_types = {
    "Di-Series": {"amount": 1},
    "Tri-Series": {"amount": 2},
    "Qui-Series": {"amount": 5},
    "Qua-Series": {"amount": 10},
    "Vle-Series": {"amount": 20},
    "Six-Series": {"amount": 30},
    "Sep-Series": {"amount": 50},
    "Oct-Series": {"amount": 60},
    "Nin-Series": {"amount": 100},
    "Who-Series": {"amount": 1000}
}

# Define Plant Types and Substances
plant_types = {
    "chem": {"substances": ["Acid", "Liquid Glass"], "produces": ["Tri-Series", "Qui-Series"]},
    "biochem": {"substances": ["U-Acid", "Bio-Liquid"], "produces": ["Six-Series", "Sep-Series"]},
    "ultrachem": {"substances": ["Ultra-Acid", "Quantum Glass"], "produces": ["Oct-Series", "Nin-Series", "Who-Series"]}
}

# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists!"}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    new_wallet = Wallet(user_id=new_user.id)
    db.session.add(new_wallet)
    db.session.commit()

    return jsonify({"message": "User registered!"}), 201

# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

# Get User Wallet
@app.route('/wallet/<int:user_id>', methods=['GET'])
def get_wallet(user_id):
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if wallet:
        return jsonify({"balance": wallet.balance, "last_earning_date": wallet.last_earning_date}), 200
    else:
        return jsonify({"message": "Wallet not found!"}), 404

# Earning Loops Daily
@app.route('/earn_loops/<int:user_id>', methods=['POST'])
def earn_loops(user_id):
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        return jsonify({"message": "Wallet not found!"}), 404
    
    now = datetime.utcnow()
    if wallet.last_earning_date.date() < now.date():
        # Update balance
        loop_amount = 1  # Default amount
        wallet.balance += loop_amount
        wallet.last_earning_date = now
        db.session.commit()
        return jsonify({"message": f"Earned {loop_amount} loop(s)!"}), 200
    else:
        return jsonify({"message": "Already earned today!"}), 400

# Create Loop Type Route
@app.route('/create_loop_type', methods=['POST'])
def create_loop_type():
    data = request.json
    loop_type = data.get('type')
    if loop_type in loop_types:
        new_loop = Loop(type=loop_type, amount=loop_types[loop_type]['amount'])
        db.session.add(new_loop)
        db.session.commit()
        return jsonify({"message": f"Loop {loop_type} created!"}), 201
    else:
        return jsonify({"message": "Invalid loop type!"}), 400

# Create Plant Route
@app.route('/create_plant', methods=['POST'])
def create_plant():
    data = request.json
    plant_type = data.get('type')
    substance = data.get('substance')
    produces = data.get('produces')
    if plant_type in plant_types and substance in plant_types[plant_type]['substances']:
        new_plant = Plant(
            type=plant_type,
            production_rate=data['production_rate'],
            substance=substance,
            produces=produces
        )
        db.session.add(new_plant)
        db.session.commit()
        return jsonify({"message": "Plant created!"}), 201
    else:
        return jsonify({"message": "Invalid plant type or substance!"}), 400

# Get All Loops
@app.route('/loops', methods=['GET'])
def get_loops():
    loops = Loop.query.all()
    return jsonify([{'type': l.type, 'amount': l.amount} for l in loops])

# Get All Plants
@app.route('/plants', methods=['GET'])
def get_plants():
    plants = Plant.query.all()
    return jsonify([{'type': p.type, 'production_rate': p.production_rate, 'substance': p.substance, 'produces': p.produces} for p in plants])

# Plant Production Logic
@app.route('/produce_loops/<int:plant_id>', methods=['POST'])
def produce_loops(plant_id):
    plant = Plant.query.get(plant_id)
    if not plant:
        return jsonify({"message": "Plant not found!"}), 404
    
    loop_amount = loop_types[plant.produces]['amount']
    loops = Loop.query.filter_by(type=plant.produces).first()
    
    if loops:
        loops.amount += plant.production_rate
    else:
        new_loop = Loop(type=plant.produces, amount=plant.production_rate)
        db.session.add(new_loop)
    
    db.session.commit()
    return jsonify({"message": f"Produced {plant.production_rate} of {plant.produces}!"}), 200

# Update Loop Type Route
@app.route('/update_loop_type/<loop_type>', methods=['PUT'])
def update_loop_type(loop_type):
    data = request.json
    if loop_type in loop_types:
        loop = Loop.query.filter_by(type=loop_type).first()
        if loop:
            loop.amount = data['amount']
            db.session.commit()
            return jsonify({"message": f"Loop {loop_type} updated!"}), 200
        else:
            return jsonify({"message": "Loop type not found!"}), 404
    else:
        return jsonify({"message": "Invalid loop type!"}), 400

# Update Plant Route
@app.route('/update_plant/<int:plant_id>', methods=['PUT'])
def update_plant(plant_id):
    data = request.json
    plant = Plant.query.get(plant_id)
    if plant:
        plant.production_rate = data['production_rate']
        db.session.commit()
        return jsonify({"message": "Plant updated!"}), 200
    else:
        return jsonify({"message": "Plant not found!"}), 404

# Default Route for Testing
@app.route('/')
def index():
    return "Welcome to the Loops API! Available routes: /loops, /plants, /create_loop_type, /create_plant, /produce_loops/<plant_id>, /update_loop_type/<loop_type>, /update_plant/<int:plant_id>, /register, /login, /wallet/<user_id>, /earn_loops/<user_id>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
