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

@require_jwt
def employee_get_balance(req: HttpRequest, employee_id: int) -> JsonResponse:
    """ Get employee balance """
    if req.method != "GET":
        return JsonResponse({"error":"Method not allowed"}, status=405)
    try:
        e = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({"error":"Not found"}, status=404)
    return JsonResponse({"balance": e.balance}, status=200)

@require_jwt
def employee_get_self(req: HttpRequest) -> JsonResponse:
    """ Get self infos """
    if req.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        e = Employee.objects.get(user_id=req.user.id)
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)
    return JsonResponse({"employee": {
        "id": e.id,
        "user": e.user_id,
        "balance": e.balance,
        "employer": e.employer
    }}, status=200)

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

        if Employee.objects.filter(user = user).exists():
            return JsonResponse({"error": "Already exists"}, status=400)

        employee = Employee.objects.create(
            user     = user,
            employer = employer,
        )

        return JsonResponse({
            "message":"Successfully created employee",
            "employee": {
                "id"  : employee.id,
                "user": employee.user.username,
                "balance": employee.balance,
                "employer": employee.employer
            }
        }, status=200)

    def get(
            self: "EmployeesView",
            req : HttpRequest
        ) -> JsonResponse:

        es = Employee.objects.all().values(
            "id", "user_id", "balance", "employer"
        )
        return JsonResponse({
            "employees": list(es)
        }, status=200)

@method_decorator(require_jwt, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class SingleEmployeeView(View):
    def get(
            self: "SingleEmployeeView",
            req : HttpRequest,
            employee_id  : int
        ) -> JsonResponse:

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)

        return JsonResponse({
            "employee": {
                "id": employee.id,
                "user_id": employee.user_id,
                "balance": employee.balance,
                "employer": employee.employer
            }
        }, status=200)

    def delete(
            self       : "SingleEmployeeView",
            req        : HttpRequest,
            employee_id: int
        ) -> JsonResponse:

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)

        if employee.user_id != req.user.id and not (req.user.is_staff or req.user.is_superuser):
            return JsonResponse({"error": "Forbidden"}, status=403)

        employee.delete()

        return JsonResponse({"message": f"Successfully deleted employee {employee_id}"}, status=200)
