# Note — régularisation des soldes négatifs (retrait du découvert -150€)

Méthode retenue : **abondement de régularisation** à la charge du Ministère, une
transaction `ABONDMENT` par salarié en négatif, d'un montant égal à la valeur absolue
de son solde. Ni contre-écriture ligne à ligne, ni réécriture de l'historique.

Justification : les transactions sont strictement immuables (`Transaction.save()`
refuse toute modification) — reconstruire quels paiements passés « n'auraient pas dû »
avoir lieu est donc impossible et non souhaitable. Un abondement unique par salarié
laisse l'historique des paiements intact, produit une ligne d'audit datée et typée, et
rend le coût total directement sommable pour le Ministère.

Implémentation : migration `wallet.0005`, exécutée avant la restauration de la
contrainte `balance >= 0`. Requête sur `balance < 0` — idempotente par construction,
un second passage ne trouve plus personne à créditer.

Coût : sur la base actuelle du dépôt (`db.sqlite3`), 0 salarié en négatif, coût
0,00 €. Ce chiffre doit être vérifié sur la base réelle avant l'envoi à Thomas — la
migration affiche le détail par salarié à l'exécution (`manage.py migrate wallet`).
