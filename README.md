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

Concernant l'attaque :
On fait :
```bash
sqlite3 tchai.db 
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

**Méthode de Hachage :** Le hash est calculé sur la représentation JSON triée et encodée en UTF-8 du tuple de la transaction (P1, P2, t, a).

### Curl

Pour recalculer les hash, on utilise la commande :
```bash
curl -X GET http://127.0.0.1:5000/api/transactions/integrity
```

