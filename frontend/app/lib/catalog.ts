import { API_URL, ApiError } from "./api";
import { SEED_DECISIONS } from "./seed";

export type PartnerStatus = "pending" | "active" | "suspended" | "closed";

export type Partner = {
    id: number;
    business_name: string;
    business_purpose: string;
    category: string;
    siren: string;
    address: string;
    city: string;
    latitude: number | null;
    longitude: number | null;
    status: PartnerStatus;
    is_featured: boolean;
    registered_at: string;
};

/** Partenaire tel que renvoyé par GET /api/v1/partners/ (catégorie imbriquée). */
type ApiPartner = {
    id: number;
    business_name: string;
    business_purpose: string;
    category: { id: number; name: string } | null;
    siren: string;
    address: string;
    latitude: number | null;
    longitude: number | null;
    status: PartnerStatus;
    is_featured: boolean;
    registered_at: string;
};

/** Corps d'une réponse paginée DRF (toutes les listes de l'API le sont). */
type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };

/** Le modèle Partner n'a pas de champ ville séparé : dérivée du dernier segment de l'adresse. */
function cityFromAddress(address: string): string {
    const segments = address.split(",");
    return segments.length > 1 ? segments[segments.length - 1].trim() : address;
}

function toPartner(p: ApiPartner): Partner {
    return {
        id: p.id,
        business_name: p.business_name,
        business_purpose: p.business_purpose,
        category: p.category?.name ?? "Non catégorisé",
        siren: p.siren,
        address: p.address,
        city: cityFromAddress(p.address),
        latitude: p.latitude,
        longitude: p.longitude,
        status: p.status,
        is_featured: p.is_featured,
        registered_at: p.registered_at,
    };
}

/**
 * Trace d'une décision de référencement (acceptation ou refus).
 *
 * Exigence juridique : chaque décision est horodatée, porte l'identifiant de
 * l'agent qui l'a prise, et un motif écrit pour les refus.
 */
export type PartnerDecision = {
    id: number;
    partner_id: number;
    partner_name: string;
    decision: "accepted" | "rejected";
    reason: string;
    agent: string;
    created_at: string;
};

/** Salarié tel que renvoyé par GET /api/v1/employees/ (réservé aux admins). */
export type AdminEmployee = {
    id: number;
    user: number;
    balance: string;
    employer: string;
};

export type Balance = {
    amount: number;
    employer: string;
    topped_up_this_month: number;
    spent_this_month: number;
};

export type Transaction = {
    id: number;
    amount: number;
    transaction_type: "PAYMENT" | "ABONDMENT";
    validated_at: string;
    partner_id: number | null;
    partner_name: string;
    counter_entry_of: number | null;
    /** Solde du salarié juste après cette écriture. Fourni uniquement sur ses propres transactions. */
    balance_after: number | null;
    /** True si une contre-écriture existe pour cette transaction (elle a été annulée). */
    is_cancelled: boolean;
};

async function fetchJson<T>(path: string, token: string | null): Promise<T> {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${path}`, { headers });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
        const message =
            typeof data?.detail === "string" ? data.detail : "Une erreur est survenue.";
        throw new ApiError(message, res.status);
    }

    return data as T;
}

export async function getPartners(token: string | null): Promise<Partner[]> {
    const data = await fetchJson<Paginated<ApiPartner> | Partner[]>("/api/v1/partners/", token);
    return Array.isArray(data) ? data : data.results.map(toPartner);
}

/** GET /api/v1/partners/{id}/ — direct, pour ne pas dépendre de la pagination du catalogue. */
export async function getPartner(id: number, token: string | null): Promise<Partner | null> {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}/api/v1/partners/${id}/`, { headers });
    if (res.status === 404) return null;

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        const message =
            typeof data?.detail === "string" ? data.detail : "Une erreur est survenue.";
        throw new ApiError(message, res.status);
    }

    return toPartner(data as ApiPartner);
}

/**
 * GET /api/v1/partners/me/ — fiche du partenaire authentifié, quel que soit son
 * statut. À utiliser à la place de `getPartner(userId, token)` : l'identifiant
 * du compte utilisateur n'est pas celui de la fiche partenaire (deux séquences
 * distinctes), donc `getPartner` échoue dès que les deux ne coïncident pas.
 */
export async function getPartnerMe(token: string | null): Promise<Partner> {
    const data = await fetchJson<ApiPartner>("/api/v1/partners/me/", token);
    return toPartner(data);
}

/** Fiche salarié telle que renvoyée par GET /api/v1/employees/me/. */
type ApiEmployeeMe = {
    id: number;
    user: number;
    balance: string;
    employer: string;
};

/** Écriture comptable telle que renvoyée par GET /api/v1/transactions/. */
type ApiTransaction = {
    id: number;
    transaction_type: "PAYMENT" | "ABONDMENT";
    partner: number | null;
    amount: string;
    validated_at: string;
    counter_entry_of: number | null;
    balance_after: string | null;
    is_cancelled: boolean;
};

function isInCurrentMonth(iso: string): boolean {
    const date = new Date(iso);
    const now = new Date();
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
}

/**
 * GET /api/v1/employees/me/ — solde et employeur du salarié authentifié.
 *
 * Les stats "crédité/dépensé ce mois-ci" ne sont pas renvoyées par l'API : on
 * les recalcule côté client à partir de l'historique des transactions.
 */
export async function getBalance(token: string | null): Promise<Balance> {
    const employee = await fetchJson<ApiEmployeeMe>("/api/v1/employees/me/", token);
    const transactions = await getTransactions(token);
    const thisMonth = transactions.filter((t) => isInCurrentMonth(t.validated_at));

    return {
        amount: Number(employee.balance),
        employer: employee.employer,
        topped_up_this_month: thisMonth
            .filter((t) => t.transaction_type === "ABONDMENT")
            .reduce((sum, t) => sum + t.amount, 0),
        spent_this_month: thisMonth
            .filter((t) => t.transaction_type === "PAYMENT")
            .reduce((sum, t) => sum + t.amount, 0),
    };
}

/** GET /api/v1/transactions/ — historique visible par l'utilisateur authentifié (paginé côté API). */
export async function getTransactions(token: string | null): Promise<Transaction[]> {
    const data = await fetchJson<Paginated<ApiTransaction> | Transaction[]>(
        "/api/v1/transactions/",
        token,
    );
    if (Array.isArray(data)) return data;

    const partners = await getPartners(token);
    const partnerNames = new Map(partners.map((p) => [p.id, p.business_name]));

    return data.results.map((t) => ({
        id: t.id,
        amount: Number(t.amount),
        transaction_type: t.transaction_type,
        validated_at: t.validated_at,
        partner_id: t.partner,
        partner_name:
            t.partner === null
                ? "Abondement employeur"
                : partnerNames.get(t.partner) ?? `Partenaire #${t.partner}`,
        counter_entry_of: t.counter_entry_of,
        balance_after: t.balance_after === null || t.balance_after === undefined ? null : Number(t.balance_after),
        is_cancelled: t.is_cancelled,
    }));
}

/** Liste des salariés — route réelle, réservée aux comptes administrateurs (paginée). */
export async function getEmployees(token: string | null): Promise<AdminEmployee[]> {
    const data = await fetchJson<Paginated<AdminEmployee> | AdminEmployee[]>("/api/v1/employees/", token);
    return Array.isArray(data) ? data : data.results;
}

export function getPartnerDecisions(): PartnerDecision[] {
    return SEED_DECISIONS;
}

const EURO = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
});

export function formatAmount(amount: number): string {
    return EURO.format(amount);
}

export function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric",
    });
}

export function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export function monthLabel(iso: string): string {
    const label = new Date(iso).toLocaleDateString("fr-FR", {
        month: "long",
        year: "numeric",
    });
    return label.charAt(0).toUpperCase() + label.slice(1);
}

export function splitAmount(amount: number): { integer: string; cents: string } {
    const parts = EURO.formatToParts(amount);

    const integer = parts
        .filter((p) => p.type === "integer" || p.type === "group" || p.type === "minusSign")
        .map((p) => p.value)
        .join("");

    const cents = parts
        .filter((p) => p.type === "decimal" || p.type === "fraction" || p.type === "literal" || p.type === "currency")
        .map((p) => p.value)
        .join("");

    return { integer, cents };
}

export function initialsOf(name: string): string {
    const words = name.split(/[^A-Za-zÀ-ÿ]+/).filter(Boolean);
    if (words.length === 0) return "?";

    if (words.length === 1) {
        const word = words[0];
        const inner = word.slice(1).search(/[A-ZÀ-Þ]/);

        return (inner === -1 ? word.slice(0, 2) : word[0] + word[inner + 1]).toUpperCase();
    }

    return (words[0][0] + words[1][0]).toUpperCase();
}

const TINTS = ["indigo", "pink", "amber", "green", "cyan", "purple"] as const;

export type Tint = (typeof TINTS)[number];

export function tintOf(name: string): Tint {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) % 997;

    return TINTS[hash % TINTS.length];
}

export function categoriesOf(partners: Partner[]): string[] {
    return [...new Set(partners.map((p) => p.category))].sort((a, b) => a.localeCompare(b, "fr"));
}

export function matchesQuery(partner: Partner, query: string): boolean {
    const q = query.trim().toLowerCase();
    if (!q) return true;

    return [partner.business_name, partner.business_purpose, partner.city, partner.category]
        .join(" ")
        .toLowerCase()
        .includes(q);
}
