"""Extraction de l'acteur et de l'IP à partir d'une requête DRF — factorisé ici pour
que chaque point d'instrumentation (#112-120) construise ses appels à
`record_audit_event` de façon identique."""


def get_client_ip(request) -> str | None:
    """Render (et tout déploiement derrière un reverse proxy) transmet l'IP réelle
    via `X-Forwarded-For` ; on ne garde que le premier maillon (le client)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def actor_info(request) -> tuple[int | None, str]:
    """(actor_id, actor_role) de l'utilisateur authentifié de la requête, ou
    (None, "") pour un appel anonyme (ex. inscription, connexion échouée)."""
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return None, ""
    return user.id, getattr(user, "role", "")
