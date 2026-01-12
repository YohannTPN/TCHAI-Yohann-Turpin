import os
import json
import hashlib
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tchai4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modèles de Base de Données ---

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    solde = db.Column(db.Float, default=0.0)
    cle_publique = db.Column(db.Text, nullable=False) # Ajout du stockage de la clé PEM

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    p1_nom = db.Column(db.String(80), nullable=False)
    p2_nom = db.Column(db.String(80), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    hash = db.Column(db.String(64), unique=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id, 'P1': self.p1_nom, 'P2': self.p2_nom,
            'a': self.montant, 't': self.timestamp.isoformat(), 'hash': self.hash
        }

# --- Initialisation Automatique via PEM ---

with app.app_context():
    db.create_all()
    
    # On scanne le dossier pour trouver des clés publiques
    for filename in os.listdir('.'):
        if filename.endswith('_public.pem'):
            nom_client = filename.replace('_public.pem', '')
            
            # Si le client n'existe pas encore en BDD
            if not db.session.execute(db.select(Client).filter_by(nom=nom_client)).scalar_one_or_none():
                with open(filename, 'r') as f:
                    pem_data = f.read()
                
                # Création avec un solde par défaut (ex: 100.0 pour les tests)
                nouveau_client = Client(nom=nom_client, solde=100.0, cle_publique=pem_data)
                db.session.add(nouveau_client)
                print(f"Client importé depuis PEM : {nom_client}")
    
    db.session.commit()

TIMESTAMP_FORMAT_HASH = "%Y-%m-%dT%H:%M:%S.%f"

# --- Utilitaires ---

def calculer_hash_transaction(p1, p2, montant, timestamp_str, hash_precedent):
    data = {"P1": p1, "P2": p2, "t": timestamp_str, "a": montant, "prev_h": hash_precedent}
    encoded = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()

# --- Routes API ---

@app.route('/api/transaction', methods=['POST'])
def enregistrer_transaction():
    data = request.get_json()
    try:
        p1_name = data['P1']
        p2_name = data['P2']
        amount = float(data['a'])
        signature_hex = data['signature'] 
    except KeyError:
        return jsonify({"erreur": "Champs manquants (P1, P2, a, signature)."}), 400

    # 1. Récupérer l'émetteur et sa clé publique
    p1 = db.session.execute(db.select(Client).filter_by(nom=p1_name)).scalar_one_or_none()
    p2 = db.session.execute(db.select(Client).filter_by(nom=p2_name)).scalar_one_or_none()

    if not p1 or not p2:
        return jsonify({"erreur": "Utilisateur inconnu."}), 404

    # 2. VERIFICATION DE LA SIGNATURE (Authenticité)
    try:
        # Reconstitution du message signé 
        message = f"{p1_name}{p2_name}{amount}".encode('utf-8')
        
        # Charger la clé publique PEM depuis la base de données
        public_key = serialization.load_pem_public_key(p1.cle_publique.encode('utf-8'))
        
        # Vérifier
        public_key.verify(
            bytes.fromhex(signature_hex),
            message,
            ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        return jsonify({"erreur": "Signature invalide. Accès refusé."}), 401
    except Exception as e:
        return jsonify({"erreur": f"Erreur de vérification: {str(e)}"}), 500

    # 3. VERIFICATION DU SOLDE
    if p1.solde < amount:
        return jsonify({"erreur": "Solde insuffisant."}), 403

    # 4. ENREGISTREMENT DANS LA BLOCKCHAIN
    try:
        p1.solde -= amount
        p2.solde += amount

        derniere_t = db.session.execute(db.select(Transaction).order_by(Transaction.id.desc())).scalars().first()
        hash_precedent = derniere_t.hash if derniere_t else "0"

        now = datetime.now(timezone.utc)
        ts_str = now.strftime(TIMESTAMP_FORMAT_HASH)
        h = calculer_hash_transaction(p1_name, p2_name, amount, ts_str, hash_precedent)

        nouvelle_t = Transaction(p1_nom=p1_name, p2_nom=p2_name, montant=amount, timestamp=now, hash=h)
        db.session.add(nouvelle_t)
        db.session.commit()

        return jsonify({"message": "Transaction authentifiée et enregistrée", "tx": nouvelle_t.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": "Erreur lors de l'écriture en base."}), 500


@app.route('/api/clients/wallet/<string:nom>', methods=['GET'])
def afficher_solde(nom):
    c = db.session.execute(db.select(Client).filter_by(nom=nom)).scalar_one_or_none()
    if not c: return jsonify({"erreur": "Inexistant"}), 404
    return jsonify({"Nom": c.nom, "Solde": c.solde}), 200

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
    app.run(host='0.0.0.0', port=5000, debug=True)