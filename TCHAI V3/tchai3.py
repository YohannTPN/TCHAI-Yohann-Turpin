from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import hashlib
import json


app = Flask(__name__)
# Configuration de la BDD SQLite (un fichier local nommé 'tchai3.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tchai3.db'
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
    """Représente une transaction (P1, P2, t, a, h)."""
    id = db.Column(db.Integer, primary_key=True)
    p1_nom = db.Column(db.String(80), nullable=False) # Émetteur
    p2_nom = db.Column(db.String(80), nullable=False) # Destinataire
    montant = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    hash = db.Column(db.String(64), unique=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'P1': self.p1_nom,
            'P2': self.p2_nom,
            'a': self.montant,
            't': self.timestamp.isoformat(),
            'hash': self.hash
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


TIMESTAMP_FORMAT_HASH = "%Y-%m-%dT%H:%M:%S.%f"

# --- Fonctions Utilitaires & Routes API ---
def calculer_hash_transaction(p1_nom, p2_nom, montant, timestamp_str, hash_precedent):
    """
    Calcule le hash SHA-256 du tuple (P1, P2, t, a, h_precedent).
    """
    transaction_data = {
        "P1": p1_nom,
        "P2": p2_nom,
        "t": timestamp_str,
        "a": montant,
        "prev_h": hash_precedent  
    }
    encoded_data = json.dumps(transaction_data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded_data).hexdigest()



@app.route('/')
def hello():
    return 'TCAHI1 - Système de Transaction avec BDD SQLAlchemy.\n', 200


@app.route('/api/transaction', methods=['POST'])
def enregistrer_transaction():
    data = request.get_json()
    try:
        p1_name, p2_name, amount = data['P1'], data['P2'], float(data['a'])
    except:
        return jsonify({"erreur": "Données invalides."}), 400

    try:
        p1 = db.session.execute(db.select(Client).filter_by(nom=p1_name)).scalar_one_or_none()
        p2 = db.session.execute(db.select(Client).filter_by(nom=p2_name)).scalar_one_or_none()

        if not p1 or not p2 or p1.solde < amount:
            return jsonify({"erreur": "Transaction impossible."}), 403

        p1.solde -= amount
        p2.solde += amount

        derniere_t = db.session.execute(db.select(Transaction).order_by(Transaction.id.desc())).scalars().first()
        hash_precedent = derniere_t.hash if derniere_t else "0" 

        now = datetime.now(timezone.utc)
        timestamp_hash_str = now.strftime(TIMESTAMP_FORMAT_HASH)
        
        transaction_hash = calculer_hash_transaction(p1_name, p2_name, amount, timestamp_hash_str, hash_precedent)

        nouvelle_transaction = Transaction(
            p1_nom=p1_name, p2_nom=p2_name, montant=amount, 
            timestamp=now, hash=transaction_hash
        )
        db.session.add(nouvelle_transaction)
        db.session.commit()

        return jsonify(nouvelle_transaction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


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


@app.route('/api/transactions/integrity', methods=['GET'])
def verifier_integrite():
    """
    Vérifie l'intégrité globale de la chaîne (EXERCICE 6 amélioré).
    """
    transactions = db.session.execute(db.select(Transaction).order_by(Transaction.id)).scalars().all()
    
    toutes_integres = True
    resultats = []
    # Le hash attendu pour la première transaction est "0"
    attente_hash_precedent = "0"

    for t in transactions:
        ts_str = t.timestamp.strftime(TIMESTAMP_FORMAT_HASH)
        hash_recalcule = calculer_hash_transaction(t.p1_nom, t.p2_nom, t.montant, ts_str, attente_hash_precedent)
        
        if hash_recalcule != t.hash:
            toutes_integres = False
            resultats.append({"id": t.id, "statut": "FAIL", "raison": "Chain broken or data altered"})
            # Si la chaîne est brisée, on s'arrête ou on continue pour voir l'étendue des dégâts
        else:
            resultats.append({"id": t.id, "statut": "OK"})
        
        # Le hash de la transaction actuelle devient le 'hash_precedent' pour la suivante
        attente_hash_precedent = t.hash

    return jsonify({
        "integrite": toutes_integres,
        "details": resultats
    }), 200 if toutes_integres else 409



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)