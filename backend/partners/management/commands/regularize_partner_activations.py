import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from partners.models import Partner, PartnerDecision

logger = logging.getLogger("regularize_partner_activations")

REGULARIZATION_REASON = (
    "Régularisation du 07/09 : statut actif constaté sans décision de référencement "
    "associée (circuit court-circuité). Décision consignée a posteriori pour rétablir "
    "la traçabilité du dossier ; aucun agent identifié pour la décision d'origine."
)


class Command(BaseCommand):
    """Identifie les partenaires en statut `active` sans `PartnerDecision` associée
    (activation en direct, hors circuit demande → contrôle → décision motivée) et
    consigne pour chacun une décision de régularisation.

    Le circuit lui-même n'est pas modifié : `PartnerDecisionCreateView` reste le seul
    point d'entrée applicatif pour faire passer un dossier de `pending` à `active`,
    et `PartnerUpdateSerializer` exclut explicitement le champ `status`. Ce script ne
    fait que documenter, a posteriori, les dossiers déjà actifs qui n'ont jamais eu de
    décision (édités en base ou via l'admin Django, hors API).

    Idempotent : un partenaire une fois régularisé a une `PartnerDecision`, il ne
    ressort donc plus de la requête au passage suivant.
    """

    help = "Consigne une PartnerDecision de régularisation pour les partenaires actifs sans décision."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="N'applique aucune modification, affiche seulement ce qui serait fait.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        prefix = "[DRY-RUN] " if dry_run else ""

        orphans = list(
            Partner.objects.filter(status="active")
            .exclude(decisions__decision="accepted")
            .order_by("registered_at")
        )

        for partner in orphans:
            line = f"{prefix}#{partner.id} {partner.business_name} — actif depuis le {partner.registered_at:%d/%m/%Y}, sans décision."
            logger.info(line)
            self.stdout.write(line)

        if not dry_run:
            self._regularize(orphans)

        summary = f"{prefix}Partenaires régularisés : {len(orphans)}"
        logger.info(summary)
        self.stdout.write(self.style.SUCCESS(summary))

    @transaction.atomic
    def _regularize(self, orphans):
        for partner in orphans:
            PartnerDecision.objects.create(
                partner=partner,
                decision="accepted",
                reason=REGULARIZATION_REASON,
                agent=None,
            )
