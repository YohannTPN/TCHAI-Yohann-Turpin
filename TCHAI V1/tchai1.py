from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
# Configuration de la BDD SQLite (un fichier local nommé 'tchai1.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tchai1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modèles de Base de Données ---

class Client(db.Model):
    """Représente une personne avec un solde."""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    solde = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Client {self.nom} - Solde: {self.solde:.2f}>'

class Transaction(db.Model):
    """Représente une transaction (P1, P2, t, a)."""
    id = db.Column(db.Integer, primary_key=True)
    p1_nom = db.Column(db.String(80), nullable=False) # Émetteur
    p2_nom = db.Column(db.String(80), nullable=False) # Destinataire
    montant = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'P1': self.p1_nom,
            'P2': self.p2_nom,
            'a': self.montant,
            't': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f'<Transaction {self.p1_nom} -> {self.p2_nom} de {self.montant} à {self.timestamp}>'

# --- Initialisation de la BDD et des Clients initiaux ---

with app.app_context():
    # Crée toutes les tables si elles n'existent pas
    db.create_all()

    # Initialisation des clients seulement s'ils n'existent pas déjà
    initial_clients = [
        {'nom': 'Yoyo', 'solde': 5.0},
        {'nom': 'Wiwi', 'solde': 10.0},
        {'nom': 'Elsa', 'solde': 20.0}
    ]

    for data in initial_clients:
        if not db.session.execute(db.select(Client).filter_by(nom=data['nom'])).scalar_one_or_none():
            client = Client(nom=data['nom'], solde=data['solde'])
            db.session.add(client)
    
    db.session.commit()
    print("Base de données initialisée avec les clients par défaut.")


# --- Fonctions Utilitaires & Routes API ---

@app.route('/')
def hello():
    return 'TCAHI1 - Système de Transaction avec BDD SQLAlchemy.\n', 200


@app.route('/api/transaction', methods=['POST'])
def enregistrer_transaction():
    data = request.get_json()
    try:
        p1_name = data['P1']
        p2_name = data['P2']
        amount = float(data['a'])
    except (TypeError, ValueError, KeyError):
        return jsonify({"erreur": "Données de transaction manquantes ou invalides (P1, P2, a)."}), 400

    if p1_name == p2_name or amount <= 0:
        return jsonify({"erreur": "Transaction invalide."}), 400
    
   
    try:
        p1 = db.session.execute(db.select(Client).filter_by(nom=p1_name)).scalar_one_or_none()
        p2 = db.session.execute(db.select(Client).filter_by(nom=p2_name)).scalar_one_or_none()

        if not p1 or not p2:
            return jsonify({"erreur": "Un ou les deux utilisateurs n'existent pas."}), 404

        if p1.solde < amount:
            return jsonify({"erreur": f"Solde insuffisant pour {p1_name}."}), 403

        p1.solde -= amount
        p2.solde += amount

        nouvelle_transaction = Transaction(p1_nom=p1_name, p2_nom=p2_name, montant=amount)
        db.session.add(nouvelle_transaction)

        db.session.commit()

        return jsonify({"message": "Transaction enregistrée", "transaction": nouvelle_transaction.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la transaction: {e}")
        return jsonify({"erreur": "Erreur interne lors de l'enregistrement de la transaction."}), 500


@app.route('/api/transactions', methods=['GET'])
def lister_toutes_transactions():
    transactions = db.session.execute(db.select(Transaction).order_by(Transaction.timestamp)).scalars().all()
    return jsonify([t.to_dict() for t in transactions]), 200


@app.route('/api/transactions/<string:nom_personne>', methods=['GET'])
def lister_transactions_personne(nom_personne):
    client = db.session.execute(db.select(Client).filter_by(nom=nom_personne)).scalar_one_or_none()
    if not client:
        return jsonify({"erreur": f"La personne '{nom_personne}' n'existe pas."}), 404

    transactions = db.session.execute(
        db.select(Transaction)
        .filter( (Transaction.p1_nom == nom_personne) | (Transaction.p2_nom == nom_personne) )
        .order_by(Transaction.timestamp)
    ).scalars().all()

    return jsonify([t.to_dict() for t in transactions]), 200


@app.route('/api/clients/wallet/<string:nom_personne>', methods=['GET'])
def afficher_solde(nom_personne):
    client = db.session.execute(db.select(Client).filter_by(nom=nom_personne)).scalar_one_or_none()

    if not client:
        return jsonify({"erreur": f"La personne '{nom_personne}' n'existe pas."}), 404

    return jsonify({"Nom": client.nom, "Solde": client.solde}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)