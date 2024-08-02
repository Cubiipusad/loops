from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loops.db'
db = SQLAlchemy(app)

class Loop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    production_rate = db.Column(db.Float, nullable=False)

# Create the database tables within the app context
with app.app_context():
    db.create_all()

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

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
