"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Landmark } from "lucide-react";
import Avatar from "../components/Avatar/Avatar";
import MinisterSpotlightDetail from "../components/MinisterSpotlightDetail/MinisterSpotlightDetail";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import { formatDate, getAllMinisterSpotlights } from "../lib/catalog";
import type { MinisterSpotlight } from "../lib/catalog";
import styles from "./coup-de-coeur.module.css";

/**
 * Page publique, accessible sans connexion : le lien que le Ministre peut
 * envoyer à qui il veut (presse, partenaires...) pour montrer le Coup de
 * cœur du moment (ou un ancien via ?id=), et tout l'historique, sans avoir
 * besoin d'un compte Ticket Tout.
 *
 * Un ancien Coup de cœur se retrouve via ?id=, pas via une route dynamique
 * /coup-de-coeur/[id] : le site est exporté statiquement (output: export),
 * qui ne peut pré-générer que des chemins connus au build — un id créé
 * après coup par l'admin casserait un lien ouvert directement. Une query
 * string, elle, est résolue côté client sans ce problème.
 */
function PublicSpotlightPageContent() {
    const searchParams = useSearchParams();
    const requestedId = searchParams.get("id");

    const [spotlights, setSpotlights] = useState<MinisterSpotlight[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getAllMinisterSpotlights(null)
            .then(setSpotlights)
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, []);

    const active = useMemo(() => spotlights.find((s) => s.is_active) ?? null, [spotlights]);

    const spotlight = useMemo(() => {
        if (requestedId === null) return active;
        return spotlights.find((s) => String(s.id) === requestedId) ?? active;
    }, [spotlights, active, requestedId]);

    const history = useMemo(
        () =>
            spotlights
                .filter((s) => s.id !== spotlight?.id)
                .sort((a, b) => Date.parse(b.published_at ?? "") - Date.parse(a.published_at ?? "")),
        [spotlights, spotlight],
    );

    return (
        <main id="main-content" tabIndex={-1} className={styles.page}>
            <header className={styles.topbar}>
                <span className={styles.brand}>Ticket Tout</span>
                <SimulationBadge size="sm" />
            </header>

            {requestedId !== null && (
                <Link href="/coup-de-coeur" className={styles.back}>
                    Le Coup de cœur du moment
                </Link>
            )}

            {error && <p className={styles.info} role="alert">{error}</p>}

            {loading ? (
                <p className={styles.info}>Chargement…</p>
            ) : (
                <>
                    {!spotlight ? (
                        <div className={styles.empty}>
                            <Landmark aria-hidden="true" />
                            <p className={styles.emptyTitle}>Aucun Coup de cœur en ce moment</p>
                            <p className={styles.emptyHint}>
                                Le Ministre n&apos;a pas encore choisi de partenaire à mettre en avant.
                            </p>
                        </div>
                    ) : (
                        <MinisterSpotlightDetail spotlight={spotlight} />
                    )}

                    {history.length > 0 && (
                        <section className={styles.history}>
                            <h2 className={styles.historyTitle}>Les précédents Coups de cœur</h2>
                            <p className={styles.historyHint}>Cliquez sur un partenaire pour retrouver sa fiche.</p>

                            <ul className={styles.historyList}>
                                {history.map((entry) => (
                                    <li key={entry.id}>
                                        <Link
                                            href={`/coup-de-coeur?id=${entry.id}`}
                                            className={styles.historyEntry}
                                        >
                                            <Avatar name={entry.partner.business_name} size="sm" />
                                            <div className={styles.historyBody}>
                                                <p className={styles.historyName}>{entry.partner.business_name}</p>
                                                <p className={styles.historyMessage}>« {entry.message} »</p>
                                                {entry.published_at && (
                                                    <p className={styles.historyDate}>
                                                        {formatDate(entry.published_at)}
                                                    </p>
                                                )}
                                            </div>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </section>
                    )}

                    <p className={styles.footnote}>
                        Ticket Tout est un dispositif de simulation à but pédagogique — aucune
                        transaction réelle n&apos;a lieu.
                    </p>
                </>
            )}
        </main>
    );
}

export default function PublicSpotlightPage() {
    return (
        <Suspense fallback={null}>
            <PublicSpotlightPageContent />
        </Suspense>
    );
}
