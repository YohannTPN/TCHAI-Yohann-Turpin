import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

def generer_paire_cles(nom_client):
    # 1. Génération de la clé privée sur la courbe SECP256K1
    private_key = ec.generate_private_key(ec.SECP256K1())
    
    # 2. Dérivation de la clé publique
    public_key = private_key.public_key()

    # 3. Sauvegarde de la clé privée dans un fichier PEM
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # 4. Sauvegarde de la clé publique dans un fichier PEM
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Écriture des fichiers
    with open(f"{nom_client}_private.pem", "wb") as f:
        f.write(private_pem)
    with open(f"{nom_client}_public.pem", "wb") as f:
        f.write(public_pem)

    print(f"Clés générées pour {nom_client} :")
    print(f" - {nom_client}_private.pem")
    print(f" - {nom_client}_public.pem")

if __name__ == "__main__":
    nom = input("Entrez le nom du client pour générer ses clés : ")
    generer_paire_cles(nom)