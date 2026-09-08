# Journal d'audit — export signé et vérification hors ligne (#124, #125)

## Export

```bash
AUDIT_EXPORT_HMAC_KEY=<clé> python manage.py export_audit_log \
    --start 2026-09-08T00:00:00 --end 2026-09-09T00:00:00 \
    --output export.json
```

`--start`/`--end` sont optionnels (filtrent sur `occurred_at`, ISO 8601). Le fichier
produit contient l'ensemble des champs de chaque enregistrement (y compris `hash` et
`prev_hash`), un `chain_digest` (résumé rapide de la période), et une signature
`hmac_sha256` calculée sur l'ensemble du contenu (hors la signature elle-même).

## Vérification, sans base de données

```bash
python audit/verify_export.py --file export.json --key <clé>
```

Aucune dépendance à Django ni à une connexion base — seuls le fichier et la clé sont
nécessaires (`audit/hashing.py`, qu'il importe, est du Python pur). Rapporte deux
vérifications distinctes :

- **Signature** : le fichier exporté a-t-il été modifié après l'export ? (intégrité
  du transport)
- **Chaîne** : les enregistrements eux-mêmes ont-ils été altérés en base *avant*
  l'export ? C'est cette vérification qui détecte et localise précisément une
  modification (« hash stocké ≠ hash recalculé sur l'id X ») ou une suppression
  (« rupture de chaîne entre l'id X et l'id Y ») — les deux cas sont distingués.

## Vérifié manuellement (scénario de la démonstration de jeudi)

1. Chaîne intacte → export → vérification : `CONFORME`.
2. Un enregistrement modifié directement en base (SQL brut, rôle privilégié) → export
   → vérification : signature toujours `CONFORME` (l'export re-signe fidèlement l'état
   actuel de la base), chaîne `NON CONFORME`, désigne l'id exact modifié.
3. Un enregistrement supprimé directement en base → export → vérification : chaîne
   `NON CONFORME`, rapporté comme une rupture de chaîne entre les deux id encadrants
   (« suppression probable »), explicitement différencié du cas modification.

Ces trois scénarios sont couverts par des tests automatisés
(`tests/test_audit_export_verify.py`) et ont été rejoués manuellement de bout en bout.
