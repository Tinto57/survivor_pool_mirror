from utils.get_payload import get_payload
from utils.wrappers import require_jwt
from django.views import View
from functools import wraps
from django.utils.decorators import method_decorator
from django.http import HttpRequest, JsonResponse
from transactions.models import Transaction
from django.utils import timezone

class SingleTransactionView(View):
    ...


@method_decorator(require_jwt, name='dispatch')
class TransactionsView(View):
    def post(
            self: "TransactionsView",
            req : HttpRequest
        ) -> JsonResponse:

        payload = get_payload(req)

        Transaction.objects.create(
            qr_code      = payload.get("qr_code"),
            employee     = payload.get("employee"),
            partner      = payload.get("partner"),
            amount       = payload.get("amount"),
            validated_at = timezone.now(),
            is_cancelled = False
        ).save()

        return JsonResponse({
            "message": "ok"
        }, status=200)
