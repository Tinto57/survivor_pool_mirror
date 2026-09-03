/**
 * Client HTTP de l'API Ticket Tout.
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

/** Fiche partenaire créée à l'inscription, en attente de validation par le Ministère. */
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

export type UserResponse = {
    user: Required<ApiUser>;
};

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
            typeof data?.error === "string" ? data.error : "Une erreur est survenue.";
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
