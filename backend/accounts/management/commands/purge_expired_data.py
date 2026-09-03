import calendar
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from partners.models import PartnerDecision
from transactions.models import QRCode

User = get_user_model()
logger = logging.getLogger("purge_expired_data")

RETENTION_MONTHS = 13


def months_ago(months, from_dt=None):
    """Date correspondant à `from_dt` moins `months` mois calendaires (pas une approximation en jours)."""
    from_dt = from_dt or timezone.now()

    month = from_dt.month - months
    year = from_dt.year
    while month <= 0:
        month += 12
        year -= 1

    last_day = calendar.monthrange(year, month)[1]
    return from_dt.replace(year=year, month=month, day=min(from_dt.day, last_day))


class Command(BaseCommand):
    """Purge et anonymise les données selon la politique de conservation de 13 mois (art. 30 RGPD).

    Applique, dans l'ordre décrit dans le registre RGPD :
    1. Suppression immédiate des QR codes expirés et jamais utilisés.
    2. Anonymisation des comptes inactifs depuis 13 mois (le lien vers la
       personne est rompu, les transactions et montants restent intacts).
    3. Suppression des comptes créés il y a 13 mois et jamais utilisés.
    4. Dissociation de l'agent sur les décisions de référencement de plus de 13 mois.

    Idempotent : peut être relancée sans effet sur les enregistrements déjà traités.
    """

    help = "Purge/anonymise les données conformément à la politique de conservation de 13 mois."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="N'applique aucune modification, affiche seulement ce qui serait fait.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        cutoff = months_ago(RETENTION_MONTHS, now)

        qr_count = self._purge_expired_qrcodes(now, dry_run)
        anonymized_count = self._anonymize_inactive_users(cutoff, dry_run)
        deleted_count = self._delete_never_used_accounts(cutoff, dry_run)
        decision_count = self._dissociate_old_decisions(cutoff, dry_run)

        prefix = "[DRY-RUN] " if dry_run else ""
        summary = (
            f"{prefix}QR codes expirés supprimés : {qr_count} · "
            f"Comptes anonymisés : {anonymized_count} · "
            f"Comptes jamais utilisés supprimés : {deleted_count} · "
            f"Décisions dissociées de leur agent : {decision_count}"
        )

        logger.info(summary)
        self.stdout.write(self.style.SUCCESS(summary))

    def _purge_expired_qrcodes(self, now, dry_run):
        """QR codes expirés et non consommés : aucune valeur probante, purge immédiate."""
        queryset = QRCode.objects.filter(expires_at__lt=now, is_used=False)
        count = queryset.count()

        if not dry_run and count:
            queryset.delete()

        return count

    @transaction.atomic
    def _anonymize_inactive_users(self, cutoff, dry_run):
        """Rompt le lien vers la personne pour les comptes déjà utilisés puis
        inactifs depuis 13 mois. Les montants et transactions ne sont pas touchés :
        seuls les champs identifiants du compte le sont."""
        queryset = User.objects.filter(
            last_login__lt=cutoff,
            is_active=True,
        ).exclude(username__startswith="anonymise-")
        count = queryset.count()

        if dry_run:
            return count

        for user in queryset:
            user.username = f"anonymise-{user.pk}"
            user.first_name = ""
            user.last_name = ""
            user.email = ""
            user.is_active = False
            user.save(update_fields=["username", "first_name", "last_name", "email", "is_active"])

        return count

    @transaction.atomic
    def _delete_never_used_accounts(self, cutoff, dry_run):
        """Un compte jamais utilisé (aucune connexion) 13 mois après sa création
        n'a plus d'utilité : suppression complète, y compris son solde."""
        queryset = User.objects.filter(last_login__isnull=True, date_joined__lt=cutoff)
        count = queryset.count()

        if not dry_run and count:
            queryset.delete()

        return count

    @transaction.atomic
    def _dissociate_old_decisions(self, cutoff, dry_run):
        """Le motif d'une décision de référencement est conservé (utilité
        probatoire), mais l'agent qui l'a prise n'est plus identifiable après 13 mois."""
        queryset = PartnerDecision.objects.filter(created_at__lt=cutoff, agent__isnull=False)
        count = queryset.count()

        if not dry_run and count:
            queryset.update(agent=None)

        return count
