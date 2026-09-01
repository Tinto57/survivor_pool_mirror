from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from utils.get_payload import get_payload
from utils.wrappers import require_jwt
from accounts.models import User
from wallet.models import Employee
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@method_decorator(require_jwt, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class EmployeesView(View):

    def post(
            self: "EmployeesView",
            req : HttpRequest
        ) -> JsonResponse:

        payload = get_payload(req)

        uid      = payload.get("user_id", None)
        employer = payload.get("employer", None)

        if not uid or not employer:
            return JsonResponse({
                "error":"Bad request"
            }, status=400)

        try:
            user: User = User.objects.get(id=uid)
        except User.DoesNotExist:
            return JsonResponse({
                "error":"User not found"
            }, status=404)

        employee = Employee.objects.create(
            user     = user,
            employer = employer,
        )

        employee.save()

        return JsonResponse({
            "message":"Successfully created employee",
            "employee": {
                "id"  : employee.id,
                "user": employee.user.username,
                "amount": employee.balance,
                "employer": employee.employer
            }
        }, status=200)
