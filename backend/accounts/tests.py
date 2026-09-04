from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.management.commands.purge_expired_data import RETENTION_MONTHS, months_ago
from partners.models import Category, Partner, PartnerDecision
from transactions.models import QRCode
from wallet.models import Employee

User = get_user_model()


def days_ago(days):
    return timezone.now() - timedelta(days=days)


class MonthsAgoTests(TestCase):
    def test_handles_year_rollover(self):
        reference = timezone.datetime(2026, 3, 15, tzinfo=timezone.get_current_timezone())
        self.assertEqual(months_ago(13, reference).year, 2025)
        self.assertEqual(months_ago(13, reference).month, 2)

    def test_clamps_day_to_shorter_month(self):
        # 31 août - 6 mois = 28/29 février, pas un 31 février inexistant.
        reference = timezone.datetime(2026, 8, 31, tzinfo=timezone.get_current_timezone())
        result = months_ago(6, reference)
        self.assertEqual(result.month, 2)
        self.assertLessEqual(result.day, 29)


class PurgeExpiredQrCodesTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="salarie1", password="x", role="employee")
        self.employee = Employee.objects.create(user=user, employer="Test SA", balance=50)

    def _make_qrcode(self, expires_delta, is_used):
        qr = QRCode.objects.create(employee=self.employee, amount=10)
        # expires_at est calculé dans save() : on le force après coup.
        QRCode.objects.filter(pk=qr.pk).update(
            expires_at=timezone.now() + expires_delta, is_used=is_used
        )
        return qr

    def test_deletes_expired_unused_qrcode(self):
        self._make_qrcode(timedelta(minutes=-10), is_used=False)

        call_command("purge_expired_data")

        self.assertEqual(QRCode.objects.count(), 0)

    def test_keeps_expired_but_used_qrcode(self):
        self._make_qrcode(timedelta(minutes=-10), is_used=True)

        call_command("purge_expired_data")

        self.assertEqual(QRCode.objects.count(), 1)

    def test_keeps_unexpired_qrcode(self):
        self._make_qrcode(timedelta(minutes=10), is_used=False)

        call_command("purge_expired_data")

        self.assertEqual(QRCode.objects.count(), 1)

    def test_dry_run_deletes_nothing(self):
        self._make_qrcode(timedelta(minutes=-10), is_used=False)

        call_command("purge_expired_data", "--dry-run")

        self.assertEqual(QRCode.objects.count(), 1)


class AnonymizeInactiveUsersTests(TestCase):
    def _make_user(self, username, last_login_days_ago):
        user = User.objects.create_user(
            username=username,
            password="x",
            role="employee",
            first_name="Jean",
            last_name="Dupont",
            email=f"{username}@example.com",
        )
        User.objects.filter(pk=user.pk).update(last_login=days_ago(last_login_days_ago))
        return User.objects.get(pk=user.pk)

    def test_anonymizes_user_inactive_since_13_months(self):
        user = self._make_user("inactif", last_login_days_ago=400)

        call_command("purge_expired_data")

        user.refresh_from_db()
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "")
        self.assertTrue(user.username.startswith("anonymise-"))
        self.assertFalse(user.is_active)

    def test_keeps_recently_active_user_untouched(self):
        user = self._make_user("actif", last_login_days_ago=30)

        call_command("purge_expired_data")

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Jean")
        self.assertTrue(user.is_active)

    def test_boundary_just_before_13_months_is_not_anonymized(self):
        # 13 mois calendaires ~ 395-396 jours selon les mois traversés ;
        # 390 jours est toujours strictement en-deçà du seuil.
        user = self._make_user("limite", last_login_days_ago=390)

        call_command("purge_expired_data")

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Jean")

    def test_does_not_reanonymize_already_anonymized_user(self):
        user = self._make_user("dejafait", last_login_days_ago=400)
        User.objects.filter(pk=user.pk).update(
            username=f"anonymise-{user.pk}", first_name="", last_name="", email="", is_active=False
        )

        # Ne doit pas planter sur un doublon de username ni retraiter la ligne.
        call_command("purge_expired_data")

        self.assertEqual(User.objects.filter(pk=user.pk).count(), 1)

    def test_dry_run_anonymizes_nothing(self):
        user = self._make_user("inactif", last_login_days_ago=400)

        call_command("purge_expired_data", "--dry-run")

        user.refresh_from_db()
        self.assertEqual(user.first_name, "Jean")
        self.assertTrue(user.is_active)


class DeleteNeverUsedAccountsTests(TestCase):
    def _make_user(self, username, date_joined_days_ago):
        user = User.objects.create_user(username=username, password="x", role="employee")
        User.objects.filter(pk=user.pk).update(
            date_joined=days_ago(date_joined_days_ago), last_login=None
        )
        return user

    def test_deletes_account_never_used_after_13_months(self):
        user = self._make_user("jamaisutilise", date_joined_days_ago=400)
        Employee.objects.create(user=user, employer="Test SA", balance=0)

        call_command("purge_expired_data")

        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(Employee.objects.filter(user_id=user.pk).exists())

    def test_keeps_recently_created_never_used_account(self):
        user = self._make_user("recent", date_joined_days_ago=10)

        call_command("purge_expired_data")

        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_keeps_old_account_that_was_used(self):
        user = User.objects.create_user(username="futilise", password="x", role="employee")
        User.objects.filter(pk=user.pk).update(
            date_joined=days_ago(400), last_login=days_ago(400)
        )

        call_command("purge_expired_data")

        # Utilisé une fois puis inactif 13 mois : anonymisé, pas supprimé.
        user.refresh_from_db()
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_dry_run_deletes_nothing(self):
        user = self._make_user("jamaisutilise", date_joined_days_ago=400)

        call_command("purge_expired_data", "--dry-run")

        self.assertTrue(User.objects.filter(pk=user.pk).exists())


class DissociatePartnerDecisionsTests(TestCase):
    def setUp(self):
        self.agent = User.objects.create_user(username="agent1", password="x", role="admin")
        partner_user = User.objects.create_user(username="partenaire1", password="x", role="partner")
        category = Category.objects.create(name="Culture")
        self.partner = Partner.objects.create(
            status="active",
            user=partner_user,
            business_name="Librairie Test",
            siren="123456789",
            business_purpose="Livres",
            category=category,
            address="1 rue de Test",
        )

    def _make_decision(self, created_at_days_ago):
        decision = PartnerDecision.objects.create(
            partner=self.partner, decision="accepted", reason="Conforme", agent=self.agent
        )
        PartnerDecision.objects.filter(pk=decision.pk).update(
            created_at=days_ago(created_at_days_ago)
        )
        return decision

    def test_dissociates_agent_after_13_months(self):
        decision = self._make_decision(created_at_days_ago=400)

        call_command("purge_expired_data")

        decision.refresh_from_db()
        self.assertIsNone(decision.agent)
        self.assertEqual(decision.reason, "Conforme")

    def test_keeps_recent_decision_agent(self):
        decision = self._make_decision(created_at_days_ago=30)

        call_command("purge_expired_data")

        decision.refresh_from_db()
        self.assertEqual(decision.agent, self.agent)

    def test_dry_run_dissociates_nothing(self):
        decision = self._make_decision(created_at_days_ago=400)

        call_command("purge_expired_data", "--dry-run")

        decision.refresh_from_db()
        self.assertEqual(decision.agent, self.agent)
