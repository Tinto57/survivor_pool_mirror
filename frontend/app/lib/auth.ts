import type { ApiUser, Role, Tokens } from "./api";

const ACCESS_KEY = "cartepro.access";
const REFRESH_KEY = "cartepro.refresh";
const ROLE_KEY = "cartepro.role";

/** Page d'accueil de chaque rôle, en un seul endroit. */
const ROLE_HOME: Record<Role, string> = {
    employee: "/employee",
    partner: "/partner",
    admin: "/admin",
};

/** Libellés repris des ROLE_CHOICES du modèle accounts.User. */
export const ROLE_LABEL: Record<Role, string> = {
    employee: "Salarié",
    partner: "Partenaire",
    admin: "Admin",
};

/** Sans rôle connu, il n'y a pas d'espace à afficher : retour à la connexion. */
export function homePathForRole(role: Role | null): string {
    return (role && ROLE_HOME[role]) ?? "/login";
}

function isBrowser(): boolean {
    return typeof window !== "undefined";
}

export function storeTokens(tokens: Tokens): void {
    if (!isBrowser()) return;
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
}

export function getAccessToken(): string | null {
    return isBrowser() ? localStorage.getItem(ACCESS_KEY) : null;
}

export function getRefreshToken(): string | null {
    return isBrowser() ? localStorage.getItem(REFRESH_KEY) : null;
}

export function clearTokens(): void {
    if (!isBrowser()) return;
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(ROLE_KEY);
}

/** Le rôle n'est pas dans le JWT : on le garde de côté à la connexion. */
export function storeRole(role: Role): void {
    if (!isBrowser()) return;
    localStorage.setItem(ROLE_KEY, role);
}

export function getCurrentRole(): Role | null {
    const role = isBrowser() ? localStorage.getItem(ROLE_KEY) : null;

    return role === "employee" || role === "partner" || role === "admin" ? role : null;
}

/** Enregistre la session complète renvoyée par /api/auth ou /api/users. */
export function startSession(user: ApiUser, tokens: Tokens): void {
    storeTokens(tokens);
    storeRole(user.role);
}

/** Lit le payload d'un JWT sans vérifier la signature (la vérification reste côté API). */
function decodeToken(token: string): Record<string, unknown> | null {
    const payload = token.split(".")[1];
    if (!payload) return null;

    try {
        const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(atob(normalized));
    } catch {
        return null;
    }
}

export function getCurrentUserId(): number | null {
    const token = getAccessToken();
    if (!token) return null;

    const userId = decodeToken(token)?.user_id;
    const parsed = typeof userId === "string" ? Number(userId) : userId;

    return typeof parsed === "number" && Number.isFinite(parsed) ? parsed : null;
}

export function isAuthenticated(): boolean {
    return getAccessToken() !== null;
}

export function logout(): void {
    clearTokens();
}
