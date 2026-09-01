from django.http import HttpRequest
import json

def get_payload(req: HttpRequest) -> dict:
    """ Get dictionnary of args from a payload (json) """
    try:
        return json.loads(req.body.decode('utf-8')) if req.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
