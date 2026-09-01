/**
 * Domaine « Ticket Tout » côté salarié : partenaires, solde et transactions.
 *
 * Les modèles Django existent (partners.Partner, wallet.Employee,
 * transactions.Transaction) mais les endpoints REST correspondants ne sont pas
 * encore exposés. Chaque lecture tente donc l'API et retombe sur le jeu de
 * données de démonstration (`seed.ts`) tant que la route répond 404 / est
 * injoignable. Le jour où le back les publie, il n'y a rien à changer ici.
 */

import { API_URL, ApiError } from "./api";
import { SEED_BALANCE, SEED_PARTNERS, SEED_TRANSACTIONS } from "./seed";

export type PartnerStatus = "pending" | "active" | "suspended" | "closed";

export type Partner = {
    id: number;
    business_name: string;
    business_purpose: string;
    category: string;
    address: string;
    city: string;
    latitude: number | null;
    longitude: number | null;
    status: PartnerStatus;
    is_featured: boolean;
};

export type Balance = {
    /** Solde disponible, en euros. */
    amount: number;
    employer: string;
    /** Total crédité par l'employeur sur le mois en cours. */
    topped_up_this_month: number;
    /** Total dépensé sur le mois en cours. */
    spent_this_month: number;
};

export type Transaction = {
    id: number;
    /** Montant en euros, toujours positif : le `kind` porte le sens. */
    amount: number;
    kind: "payment" | "topup";
    /** ISO 8601. */
    validated_at: string;
    partner_id: number | null;
    partner_name: string;
    is_cancelled: boolean;
};

/**
 * Appelle l'API et retombe sur `fallback` si la route n'existe pas encore
 * (404) ou si le serveur est injoignable (status 0). Les autres erreurs
 * (401, 500...) remontent : elles méritent d'être affichées à l'utilisateur.
 */
async function fetchOrSeed<T>(path: string, token: string | null, fallback: T): Promise<T> {
    try {
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API_URL}${path}`, { headers });

        if (res.status === 404) return fallback;
        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            const message =
                typeof data?.error === "string" ? data.error : "Une erreur est survenue.";
            throw new ApiError(message, res.status);
        }

        return data as T;
    } catch (err) {
        if (err instanceof ApiError) throw err;
        return fallback;
    }
}

export function getPartners(token: string | null): Promise<Partner[]> {
    return fetchOrSeed<Partner[]>("/api/partners", token, SEED_PARTNERS);
}

export async function getPartner(id: number, token: string | null): Promise<Partner | null> {
    const partners = await getPartners(token);
    return partners.find((p) => p.id === id) ?? null;
}

export function getBalance(token: string | null): Promise<Balance> {
    return fetchOrSeed<Balance>("/api/wallet/balance", token, SEED_BALANCE);
}

export function getTransactions(token: string | null): Promise<Transaction[]> {
    return fetchOrSeed<Transaction[]>("/api/transactions", token, SEED_TRANSACTIONS);
}

/* -------------------------------------------------------------------------- */
/* Helpers d'affichage                                                        */
/* -------------------------------------------------------------------------- */

const EURO = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
});

export function formatAmount(amount: number): string {
    return EURO.format(amount);
}

/** « 12 mars 2026 » */
export function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric",
    });
}

/** « 12 mars, 14:30 » — format compact pour les listes. */
export function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    });
}

/** Clé de regroupement mensuel de l'historique : « mars 2026 ». */
export function monthLabel(iso: string): string {
    const label = new Date(iso).toLocaleDateString("fr-FR", {
        month: "long",
        year: "numeric",
    });
    return label.charAt(0).toUpperCase() + label.slice(1);
}

/**
 * Découpe un montant pour l'affichage « héro » du solde : la partie entière est
 * affichée en grand, les centimes et le symbole en plus petit — comme sur les
 * applications bancaires.
 */
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

/**
 * Monogramme d'un partenaire : initiales des deux premiers mots, ou les deux
 * premières lettres si le nom est en un seul mot. Les majuscules internes sont
 * traitées comme des débuts de mots (« KostumParty » donne « KP »).
 */
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

/** Pastilles colorées des vignettes partenaires, à la façon des avatars marchands. */
const TINTS = ["indigo", "pink", "amber", "green", "cyan", "purple"] as const;

export type Tint = (typeof TINTS)[number];

/**
 * Couleur de pastille déterministe, dérivée du nom : un même partenaire garde
 * toujours la même teinte, sans avoir à la stocker côté API.
 */
export function tintOf(name: string): Tint {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) % 997;

    return TINTS[hash % TINTS.length];
}

/** Les catégories présentes dans le catalogue, pour les filtres. */
export function categoriesOf(partners: Partner[]): string[] {
    return [...new Set(partners.map((p) => p.category))].sort((a, b) => a.localeCompare(b, "fr"));
}

/** Recherche plein texte simple sur le nom, la description, la ville et la catégorie. */
export function matchesQuery(partner: Partner, query: string): boolean {
    const q = query.trim().toLowerCase();
    if (!q) return true;

    return [partner.business_name, partner.business_purpose, partner.city, partner.category]
        .join(" ")
        .toLowerCase()
        .includes(q);
}
