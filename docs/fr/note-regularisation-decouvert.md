# Note pour Thomas — régularisation des soldes négatifs (retrait du découvert -150€)

Le découvert est supprimé : le solde ne peut plus passer sous 0€, un débit
supérieur au solde est refusé avec un message explicite (`Insufficient balance` /
`Solde insuffisant pour la contre-écriture`).

Méthode retenue pour les soldes déjà négatifs : **abondement de régularisation** à
la charge du Ministère, une transaction `ABONDMENT` par salarié en négatif, d'un
montant égal à la valeur absolue de son solde. Ni contre-écriture ligne à ligne, ni
réécriture de l'historique.

Justification : les transactions sont strictement immuables — reconstruire quels
paiements passés « n'auraient pas dû » avoir lieu est impossible. Un abondement
unique par salarié laisse l'historique intact, produit une ligne d'audit datée et
typée, et rend le coût total directement sommable.

Implémentation : migration `wallet.0005`, exécutée avant la restauration de la
contrainte `balance >= 0`. Requête sur `balance < 0` — idempotente par construction
et vérifiée (rejouée deux fois de suite sur un solde négatif simulé : régularisé une
fois, plus rien à faire au second passage). Le coût total est affiché à l'exécution
de `manage.py migrate wallet`.

Coût : à ce jour, aucun salarié en négatif connu sur les bases utilisées pour le
développement — coût 0,00 €. Ce chiffre doit être confirmé en relançant la migration
sur la base réelle avant l'envoi définitif ; elle affichera alors le détail par
salarié et le total exact.
