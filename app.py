from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loops.db'
db = SQLAlchemy(app)

# Models for the existing Loops and Plants
class Loop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    production_rate = db.Column(db.Float, nullable=False)

# Models for the new User functionality
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(64), unique=True, nullable=False)
    loops = db.Column(db.Integer, default=0, nullable=False)
    last_earned = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

# Create the database tables within the app context
with app.app_context():
    db.create_all()

# Endpoints for existing Loops and Plants
@app.route('/create_loop', methods=['POST'])
def create_loop():
    data = request.json
    new_loop = Loop(type=data['type'], amount=data['amount'])
    db.session.add(new_loop)
    db.session.commit()
    return jsonify({"message": "Loop created!"}), 201

@app.route('/create_plant', methods=['POST'])
def create_plant():
    data = request.json
    new_plant = Plant(type=data['type'], production_rate=data['production_rate'])
    db.session.add(new_plant)
    db.session.commit()
    return jsonify({"message": "Plant created!"}), 201

@app.route('/loops', methods=['GET'])
def get_loops():
    loops = Loop.query.all()
    return jsonify([{'type': l.type, 'amount': l.amount} for l in loops])

@app.route('/plants', methods=['GET'])
def get_plants():
    plants = Plant.query.all()
    return jsonify([{'type': p.type, 'production_rate': p.production_rate} for p in plants])

# Endpoints for User Management and Earning Loops
@app.route('/create_account', methods=['POST'])
def create_account():
    wallet_address = str(uuid.uuid4())  # Generate a unique wallet address
    new_user = User(wallet_address=wallet_address)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"wallet_address": wallet_address})

@app.route('/earn_loops', methods=['POST'])
def earn_loops():
    wallet_address = request.json.get('wallet_address')
    user = User.query.filter_by(wallet_address=wallet_address).first()

    if user:
        now = datetime.utcnow()
        if user.last_earned < now - timedelta(days=1):
            user.loops += 1
            user.last_earned = now
            db.session.commit()
            return jsonify({"loops": user.loops})
        else:
            return jsonify({"message": "You can only earn once every 24 hours."}), 400
    else:
        return jsonify({"message": "User not found."}), 404

@app.route('/get_balance', methods=['GET'])
def get_balance():
    wallet_address = request.args.get('wallet_address')
    user = User.query.filter_by(wallet_address=wallet_address).first()

    if user:
        return jsonify({"wallet_address": wallet_address, "loops": user.loops})
    else:
        return jsonify({"message": "User not found."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
