from flask import*
from datetime import datetime
app = Flask(__name__)

clients = [
    {'id': 0, 'Nom': 'Yoyo', 'Solde': 5.0},
    {'id': 1, 'Nom': 'Wiwi', 'Solde': 10.0},
    {'id': 2, 'Nom': 'Elsa', 'Solde': 20.0}
]

transactions = []

def get_client_by_name(nom):
    for client in clients:
        if client['Nom'].lower() == nom.lower():
            return client
    return None

def update_client_wallet(p1_name, p2_name, amount):
    p1 = get_client_by_name(p1_name)
    p2 = get_client_by_name(p2_name)

    if not p1 or not p2:
        return False, "Un ou les deux utilisateurs n'existent pas."

    if p1['Solde'] < amount:
        return False, f"Solde insuffisant pour {p1_name}."

    p1['Solde'] -= amount

    p2['Solde'] += amount

    return True, "Solde mis à jour avec succès."

@app.route('/')
def hello():
    return 'TCAHI1\n', 200

@app.route('/api/transaction', methods=['POST'])
def enregistrer_transaction():
    """
    Enregistre une nouvelle transaction et met à jour les soldes.
    Format attendu du JSON : {"P1": "Yoyo", "P2": "Wiwi", "a": 5.0}
    """
    data = request.get_json()

    if not data or 'P1' not in data or 'P2' not in data or 'a' not in data:
        return jsonify({"erreur": "Données de transaction incomplètes."}), 400

    try:
        p1 = data['P1']
        p2 = data['P2']
        amount = float(data['a'])
    except (ValueError, TypeError):
        return jsonify({"erreur": "Le montant 'a' doit être un nombre."}), 400

    if p1 == p2:
        return jsonify({"erreur": "P1 et P2 doivent être différents."}), 400


    success, message = update_client_wallet(p1, p2, amount)

    if not success:
        return jsonify({"erreur": message}), 403 


    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nouvelle_transaction = {
        'P1': p1,
        'P2': p2,
        't': t,
        'a': amount
    }
    transactions.append(nouvelle_transaction)

    return jsonify({"message": "Transaction enregistrée", "transaction": nouvelle_transaction}), 201 

@app.route('/api/transactions', methods=['GET'])
def lister_transactions():
    """
    Retourne la liste de toutes les transactions enregistrées.
    """
    return jsonify(transactions), 200

@app.route('/api/transactions/<nom>', methods=['GET'])
def lister_transactions_utilisateur(nom):
    """
    Retourne la liste des transactions impliquant l'utilisateur spécifié.
    """
    user_transactions = [
        t for t in transactions if t['P1'].lower() == nom.lower() or t['P2'].lower() == nom.lower()
    ]
    return jsonify(user_transactions), 200

@app.route('/api/clients/wallet/<nom>', methods=['GET'])
def solde(nom):
    """
    Retourne le solde du client spécifié.
    """
    client = get_client_by_name(nom)
    if not client:
        return jsonify({"erreur": "Client non trouvé."}), 404

    return jsonify({"Nom": client['Nom'], "Solde": client['Solde']}), 200




app.run(host='0.0.0.0',debug=True)