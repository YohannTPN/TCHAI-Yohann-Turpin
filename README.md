# Projet Tchaî : Système de Transactions Sécurisées

## Objectif du TP

L'objectif est de concevoir un système de registre distribué (type Blockchain) pour garantir l'intégrité globale des transactions et l'authenticité des émetteurs via le protocole HTTP.

**Auteur :** Turpin Yohann

---

## Installation et Configuration

### Dépendances

Le projet utilise **Python 3**, le framework **Flask** pour l'API, **SQLAlchemy** pour la gestion de la base de données SQLite, et **cryptography** pour les signatures numériques.

```bash
pip install Flask Flask-SQLAlchemy cryptography
```

### Utilisation sous WSL

Si vous utilisez WSL, l'adresse `127.0.0.1` peut parfois être inaccessible depuis l'hôte Windows.

1. Récupérez l'IP de votre instance WSL : `cat /etc/resolv.conf` ou `hostname -I`.
2. Remplacez `127.0.0.1` par cette IP dans vos commandes `curl`.

> **Note importante :** Pour observer l'effet des attaques et repartir sur une base saine, supprimez le fichier `.db` (ex: `rm tchai4.db`) entre chaque version ou chaque scénario d'attaque.

---

## Évolution du Système

### Tchaî v1 : Système de base

**Concept :** Enregistrement simple en base de données sans mécanisme de sécurité.

#### Commandes API

Pour créer une transaction :
```bash
curl -X POST http://127.0.0.1:5000/api/transaction \
     -H "Content-Type: application/json" \
     -d '{"P1": "Yoyo", "P2": "Wiwi", "a": 2.5}'
```

Pour lister les transactions :
```bash
curl -X GET http://127.0.0.1:5000/api/transactions
```

Pour connaître les transactions d'un client :
```bash
curl -X GET http://127.0.0.1:5000/api/transactions/<nom>
```

Pour connaître le solde d'un client :
```bash
curl -X GET http://127.0.0.1:5000/api/clients/wallet/<nom>
```

#### Attaque par Modification

1. Accédez à la base de données :
```bash
sqlite3 tchai1.db
```

2. Modifiez le montant d'une transaction :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```

**Observation :** Le solde du client est désynchronisé de l'historique sans que le système ne s'en aperçoive.

---

### Tchaî v2 : Introduction du Hachage (SHA-256)

**Concept :** Chaque transaction possède un hash calculé sur ses données (P1, P2, t, a, h) en utilisant SHA-256.

**Choix de SHA-256 :** Algorithme de hachage cryptographique standard offrant une excellente résistance aux collisions et aux attaques par préimage. Le hash est calculé sur la représentation JSON triée et encodée en UTF-8 du tuple de la transaction.

#### Vérification de l'intégrité

```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

#### Attaque par Modification

1. Accédez à la base de données :
```bash
sqlite3 tchai2.db
```

2. Modifiez le montant d'une transaction :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```

**Observation :** L'intégrité est compromise car le hash recalculé ne correspond plus au hash stocké. Le système détecte maintenant la modification.

#### Attaque par Suppression

1. Accédez à la base de données :
```bash
sqlite3 tchai2.db
```

2. Supprimez une transaction :
```bash
DELETE FROM "transaction" WHERE id = 1;
```

**Observation :** Le système vérifie l'intégrité ligne par ligne. Si une ligne disparaît, le système ne voit aucune erreur car il n'y a pas de chaînage entre les transactions.

---

### Tchaî v3 : Chaînage Cryptographique (Blockchain)

**Concept :** Le hash de la transaction n+1 dépend du hash de la transaction n, créant une chaîne cryptographique.

**Formule :** `h(n+1) = SHA256(P1 || P2 || t || a || h(n))`

#### Modifications apportées

- `calculer_hash_transaction` : Accepte maintenant un argument `hash_precedent`
- `enregistrer_transaction` : Récupère le hash de la dernière transaction en base avant de créer la nouvelle. Si c'est la première, on utilise un "hash de genèse" (ex: "0")
- `verifier_integrite` : Recalcule les hashs en cascade en utilisant le hash de l'élément précédent dans la boucle

#### Vérification de l'intégrité

```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

#### Attaque par Modification

1. Accédez à la base de données :
```bash
sqlite3 tchai3.db
```

2. Modifiez le montant d'une transaction :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```

**Observation :** L'intégrité est compromise car toute la chaîne suivante devient invalide.

#### Attaque par Suppression

1. Accédez à la base de données :
```bash
sqlite3 tchai3.db
```

2. Supprimez une transaction :
```bash
DELETE FROM "transaction" WHERE id = 1;
```

**Observation :** La suppression d'une ligne brise le chaînage (le `prev_h` de la transaction suivante devient invalide). Le système détecte maintenant cette attaque.

#### Attaque par Injection

1. Accédez à la base de données :
```bash
sqlite3 tchai3.db
```

2. Consultez les transactions existantes :
```bash
SELECT * FROM "transaction";
```

3. Récupérez le hash de la dernière transaction et calculez un hash valide pour votre fausse transaction.

4. Injectez la fausse transaction :
```bash
INSERT INTO "transaction" (p1_nom, p2_nom, montant, timestamp, hash) 
VALUES ('Wiwi', 'Elsa', 10.0, '2026-01-05 10:00:00.000000', 'fake_hash_calculé');
```

5. Mettez à jour les soldes :
```bash
UPDATE client SET solde = solde - 10.0 WHERE nom = 'Wiwi';
UPDATE client SET solde = solde + 10.0 WHERE nom = 'Elsa';
```

**Observation :** Un attaquant peut injecter une transaction s'il possède les droits sur la BDD en recalculant manuellement un hash valide. Il manque un système d'authentification.

---

## Tchaî v4 : Authenticité par Courbes Elliptiques (ECDSA)

Cette version introduit la **cryptographie asymétrique** pour s'assurer que seul le propriétaire d'un compte peut initier une dépense.
De plus, je me suis inspiré de la vidéo [viens, on recode Bitcoin - V2F](https://www.youtube.com/watch?v=U4S-RGNyTJA) afin d'implémenter le même chiffrement asymétrique que pour le BitCoin.

### Fonctionnement Mathématique (SECP256k1)

L'authentification repose sur l'algorithme **ECDSA** (Elliptic Curve Digital Signature Algorithm), utilisé par Bitcoin.

#### 1. Génération des clés

On utilise une courbe elliptique définie par l'équation `y² = x³ + 7` et un point générateur `G`.

- **Clé privée (e) :** Un nombre entier aléatoire secret (256 bits)
- **Clé publique (P) :** Un point sur la courbe tel que :

```
P = e · G
```

La clé publique est dérivée de la clé privée par multiplication scalaire sur la courbe.

#### 2. Génération de la signature

Pour signer un message (transaction), l'émetteur génère un couple `(r, s)` :

1. Génère un nombre aléatoire `k` (nonce)
2. Calcule le point `R = k · G` et prend `r = R.x` (coordonnée x de R)
3. Calcule le hash du message `z = SHA256(message)`
4. Calcule `s = k⁻¹ · (z + r · e) mod n` (où n est l'ordre de la courbe)

La signature est le couple `(r, s)`.

#### 3. Vérification de la signature

Pour vérifier qu'une transaction est authentique, le serveur utilise :
- Le hash du message `z`
- La clé publique `P` de l'émetteur
- La signature `(r, s)`

Le serveur vérifie l'égalité :

```
(z/s) · G + (r/s) · P = k · G
```

Plus précisément :
1. Calcule `u₁ = z · s⁻¹ mod n`
2. Calcule `u₂ = r · s⁻¹ mod n`
3. Calcule le point `R' = u₁ · G + u₂ · P`
4. Vérifie que `R'.x = r`

Si la coordonnée x du point résultant correspond à `r`, la signature est valide. L'émetteur prouve qu'il connaît `e` (la clé privée) sans jamais la révéler.

---

## Tutoriel : Tester la Tchaî v4

### 1. Générer les identités (Clés)

Utilisez le script `gen_keys.py` pour créer les paires de clés pour vos utilisateurs :

```bash
python gen_keys.py
# Entrez par exemple : Yoyo
```

Cela crée `Yoyo_private.pem` (à garder secret) et `Yoyo_public.pem`. Placez les fichiers `.pem` dans le dossier du serveur.

### 2. Démarrer le serveur

Lancez `tchai4.py`. Le serveur va scanner les fichiers `.pem` et créer automatiquement les clients en base de données avec leurs clés publiques respectives.

```bash
python tchai4.py
```

### 3. Signer une transaction

Avant d'envoyer une requête, l'émetteur doit signer les données avec sa clé privée :

```bash
python sign_tx.py
# Nom émetteur : Yoyo
# Nom destinataire : Wiwi
# Montant : 10
# Fichier : Yoyo_private.pem
```

Le script vous donnera une **Signature Hexadécimale**.

### 4. Envoyer la transaction via Curl

Utilisez la signature obtenue pour valider l'envoi :

```bash
curl -X POST http://127.0.0.1:5000/api/transaction \
     -H "Content-Type: application/json" \
     -d '{
         "P1": "Yoyo",
         "P2": "Wiwi",
         "a": 10.0,
         "signature": "VOTRE_SIGNATURE_HEX_ICI"
     }'
```

### 5. Vérifier l'intégrité

```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

---

### Pourquoi cette version est-elle plus sûre ?

Même si un attaquant accède à la base de données (via `sqlite3`), il ne pourra pas :

1. **Injecter de nouvelles transactions crédibles** : Sans accès aux fichiers `_private.pem` des utilisateurs, il ne peut pas générer de signatures valides
2. **Usurper l'identité d'un utilisateur** : La signature ECDSA prouve cryptographiquement que seul le détenteur de la clé privée a pu créer la transaction
3. **Modifier des transactions existantes** : Le chaînage cryptographique détecte toute modification

Toute transaction injectée sans signature valide sera immédiatement rejetée par le serveur lors de la vérification.

---
