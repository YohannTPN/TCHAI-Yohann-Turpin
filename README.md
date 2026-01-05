# TP de sécurite et cryptographie

## Objectif
Le but du TP est de concevoir un système de transactions électroniques avec une intégrité garantie, accessible par le protocole HTTP.

## Auteur
- Turpin Yohann

## Pour la BDD

pip install Flask Flask-SQLAlchemy

## Curl
### Depuis WSL
Pour obtenir l'addresse IP :
cat /etc/resolv.conf
Et remplacer par 127.0.0.1 par l'ip trouvée.

## Nota Bene
Entre chaque attaque de la base de donnée, il faudra la supprimer, puis recommencer les rêquetes Curl afin d'observer les différents types d'attaques.

## TCHAI 1
Commande pour l'API :

Pour créer une transaction
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

Concernant l'attaque par modification de transaction:
On fait :
```bash
sqlite3 tchai1.db 
```

Puis pour l'attaque :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```
Ce qui résulte en une désynchronisation entre le solde et le montant des transactions.

## TCHAI v2
### Fonction de Hachage

**Choix :** SHA-256 (Secure Hash Algorithm 256 bits)

**Justification :** Le SHA-256 est un algorithme de hachage cryptographique standard et largement reconnu. Il offre une excellente résistance aux collisions et aux attaques par préimage, ce qui garantit l'intégrité des données des transactions. La probabilité qu'une modification minime d'une transaction ne change pas son hash est considérée comme négligeable.

**Méthode de Hachage :** Le hash est calculé sur la représentation JSON triée et encodée en UTF-8 du tuple de la transaction (P1, P2, t, a, h).

### Curl

Pour recalculer les hash, on utilise la commande :
```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

Concernant l'attaque par modification de transaction:
On fait :
```bash
sqlite3 tchai2.db 
```

Puis pour l'attaque :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```

Ce qui résulte en une intégrité compromise,réglant le problème rencontré avec TCHAI1.

Concernant l'attaque par suppression de transaction:
On fait :
```bash
sqlite3 tchai2.db 
```

Puis pour l'attaque :
```bash
DELETE FROM "transaction" WHERE id = 1;
```
Ce qui par surprise, ne crée aucune erreur d'intégrité au sein de l'API.

## TCHAI v3
### Modifications apportées 
- calculer_hash_transaction : Accepte maintenant un argument hash_precedent.

- enregistrer_transaction : Récupère le hash de la dernière transaction en base avant de créer la nouvelle. Si c'est la première, on utilise un "hash de genèse" (ex: "0").

- verifier_integrite : Recalcule les hashs en cascade en utilisant le hash de l'élément précédent dans la boucle.

### Curl

Pour recalculer les hash, on utilise la commande :
```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

Concernant l'attaque par modification de transaction:
On fait :
```bash
sqlite3 tchai3.db 
```

Puis pour l'attaque :
```bash
UPDATE "transaction" SET montant = 10.0 WHERE id = 1;
```

Concernant l'attaque par suppression de transaction:
On fait :
```bash
sqlite3 tchai3.db 
```

Puis pour l'attaque :
```bash
DELETE FROM "transaction" WHERE id = 1;
```

Ce qui cette fois ci, résulte en une erreur d'intégrité.


Enfin, concernant l'attaque visant à créer une transaction entre une personne tiers et l'attaquant :
On utilise le script qui calcule le hash d'une transaction à partir du dernier hash trouvable dans la BDD.
J'ai fait :
```bash
sqlite3 tchai3.db 
```
```bash
SELECT * FROM "transaction";
```
Puis, j'ai pris le hash de la dernière transaction.
Ensuite, j'ai pu calculer le hash d'une fausse transaction entre Wiwi et Elsa.
J'ai ainsi fait :

```bash
INSERT INTO "transaction" (p1_nom, p2_nom, montant, timestamp, hash) 
VALUES ('Wiwi', 'Elsa', 10.0, '2026-01-05 10:00:00.000000','fake_hash');
```
```bash
UPDATE client SET solde = solde - 10.0 WHERE nom = 'Wiwi';
UPDATE client SET solde = solde + 10.0 WHERE nom = 'Elsa';
```

Ce qui résulte en une attaque réussi, car il n'y a pas de sytème de signature.

## TCHAI v4
