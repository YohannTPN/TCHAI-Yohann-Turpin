import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

def signer_transaction(fichier_cle_privee, p1, p2, montant):
    # 1. Charger la clé privée depuis le fichier PEM
    with open(fichier_cle_privee, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    # 2. Préparer les données à signer 
    # On crée une chaîne de caractères unique représentant la transaction
    message = f"{p1}{p2}{montant}".encode('utf-8')

    # 3. Signer le message avec ECDSA
    # La bibliothèque gère le hashage interne avec SHA256 avant la signature
    signature = private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256())
    )

    # 4. Retourner la signature en format Hexadécimal (plus facile à copier-coller dans curl)
    return signature.hex()

if __name__ == "__main__":
    print("--- Signature d'une transaction ---")
    p1 = input("Nom de l'émetteur (P1) : ")
    p2 = input("Nom du destinataire (P2) : ")
    montant = input("Montant (a) (format : 123.45) : ")
    fichier = input(f"Fichier de clé privée de {p1} (ex: {p1}_private.pem) : ")

    try:
        sig_hex = signer_transaction(fichier, p1, p2, montant)
        print("\nSignature générée (à inclure dans votre requête POST) :")
        print(sig_hex)
    except Exception as e:
        print(f"Erreur : {e}")