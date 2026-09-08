/**
 * Client HTTP de l'API CartePro.
 *
 * L'URL du backend est configurable via NEXT_PUBLIC_API_URL (voir .env.local),
 * et retombe sur le serveur de dev Django par défaut.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Tokens = {
    access: string;
    refresh: string;
};

export type Role = "employee" | "partner" | "admin";

export type ApiUser = {
    id: number;
    username: string;
    role: Role;
    first_name?: string;
    last_name?: string;
    email?: string;
};

/** Fiche partenaire créée à l'inscription, en attente de validation. */
export type ApiPartner = {
    id: number;
    business_name: string;
    status: "pending" | "active" | "suspended" | "closed";
};

export type LoginResponse = {
    message: string;
    user: ApiUser;
    token: Tokens;
};

export type RegisterResponse = {
    message: string;
    user: ApiUser;
    token: Tokens;
    partner?: ApiPartner;
};

export type UserResponse = Required<ApiUser>;

/** Erreur renvoyée par l'API, avec le code HTTP associé (0 = serveur injoignable). */
export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

type RequestOptions = {
    method?: string;
    body?: unknown;
    token?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, token } = options;

    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let res: Response;
    try {
        res = await fetch(`${API_URL}${path}`, {
            method,
            headers,
            body: body === undefined ? undefined : JSON.stringify(body),
        });
    } catch {
        // NOTE: un fetch qui échoue ne dit pas pourquoi (API éteinte, CORS, mauvaise
        //       URL...) — on affiche au moins l'URL visée pour pouvoir diagnostiquer.
        throw new ApiError(`Impossible de contacter l'API (${API_URL}). Vérifiez qu'elle est démarrée.`, 0);
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        const message =
            typeof data?.detail === "string" ? data.detail : "Une erreur est survenue.";
        throw new ApiError(message, res.status);
    }

    return data as T;
}

/** POST /api/v1/auth/ — récupère une paire de tokens JWT. */
export function login(username: string, password: string): Promise<LoginResponse> {
    return request<LoginResponse>("/api/v1/auth/", {
        method: "POST",
        body: { username, password },
    });
}

export type RegisterPayload = {
    username: string;
    password: string;
    first_name?: string;
    last_name?: string;
    email?: string;
    role?: Role;
    partner?: {
        business_name: string;
        siren: string;
        business_purpose: string;
        address: string;
        latitude: number | null;
        longitude: number | null;
    };
};

/**
 * POST /api/v1/users/ — crée le compte et renvoie directement les tokens.
 *
 * Avec role: "partner", le bloc `partner` crée la fiche entreprise en statut
 * "pending" : elle n'est visible au catalogue qu'après validation par un admin.
 */
export function register(payload: RegisterPayload): Promise<RegisterResponse> {
    return request<RegisterResponse>("/api/v1/users/", {
        method: "POST",
        body: payload,
    });
}

/** GET /api/v1/users/{id}/ — route protégée par JWT. */
export function getUser(userId: number, token: string): Promise<UserResponse> {
    return request<UserResponse>(`/api/v1/users/${userId}/`, { token });
}

export function getUserSelf(): Promise<UserResponse> {
    return request<UserResponse>(`/api/v1/users/me/`);
}

export type BalanceUpdateResponse = {
    id: number;
    balance: string;
};

/**
 * PATCH /api/v1/employees/{id}/balance/ — abondement employeur.
 *
 * Réservé aux comptes administrateurs : le montant est ajouté au solde existant.
 */
export function creditEmployee(
    employeeId: number,
    amount: number,
    token: string,
): Promise<BalanceUpdateResponse> {
    return request<BalanceUpdateResponse>(`/api/v1/employees/${employeeId}/balance/`, {
        method: "PATCH",
        body: { amount: amount.toFixed(2) },
        token,
    });
}

export type MinisterSpotlightResponse = {
    id: number;
    partner: { id: number; business_name: string; category: string; address: string };
    message: string;
    is_active: boolean;
    click_count: number;
    published_by: string | null;
    published_at: string;
};

/** POST /api/v1/ministre/coup-de-coeur/click/ — public, ne doit jamais bloquer la navigation. */
export function postSpotlightClick(): void {
    fetch(`${API_URL}/api/v1/ministre/coup-de-coeur/click/`, { method: "POST" }).catch(() => {});
}

/**
 * POST /api/v1/ministre/coup-de-coeur/historique/ — publie un nouveau Coup de cœur du
 * Ministre. Désactive automatiquement la mise en avant précédente. Réservé aux administrateurs.
 */
export function publishSpotlight(
    partnerId: number,
    message: string,
    token: string,
): Promise<MinisterSpotlightResponse> {
    return request<MinisterSpotlightResponse>("/api/v1/ministre/coup-de-coeur/historique/", {
        method: "POST",
        body: { partner: partnerId, message },
        token,
    });
}

/**
 * POST /api/v1/ministre/coup-de-coeur/{id}/republier/ — réactive une publication archivée
 * sans la recréer (le compteur de clics est conservé). Réservé aux administrateurs.
 */
export function republishSpotlight(
    spotlightId: number,
    token: string,
): Promise<MinisterSpotlightResponse> {
    return request<MinisterSpotlightResponse>(
        `/api/v1/ministre/coup-de-coeur/${spotlightId}/republier/`,
        { method: "POST", token },
    );
}

export type PartnerDecisionResponse = {
    id: number;
    partner: number;
    decision: "accepted" | "rejected";
    reason: string;
    agent: string | null;
    created_at: string;
};

/**
 * POST /api/v1/partners/{id}/decision/ — accepte ou refuse une demande de
 * référencement en attente. Réservé aux comptes administrateurs.
 */
export function decidePartner(
    partnerId: number,
    decision: "accepted" | "rejected",
    reason: string,
    token: string,
): Promise<PartnerDecisionResponse> {
    return request<PartnerDecisionResponse>(`/api/v1/partners/${partnerId}/decision/`, {
        method: "POST",
        body: reason ? { decision, reason } : { decision },
        token,
    });
}
