"use client";

import { useEffect, useMemo, useState } from "react";
import { Search, SearchX } from "lucide-react";
import Page from "../components/Page/Page";
import PartnerCard from "../components/PartnerCard/PartnerCard";
import { getAccessToken } from "../lib/auth";
import { categoriesOf, getPartners, matchesQuery } from "../lib/catalog";
import type { Partner } from "../lib/catalog";
import styles from "./catalogue.module.css";

const ALL = "Toutes";

export default function CataloguePage() {
    const [partners, setPartners] = useState<Partner[]>([]);
    const [query, setQuery] = useState("");
    const [category, setCategory] = useState(ALL);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getPartners(getAccessToken())
            .then(setPartners)
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, []);

    const categories = useMemo(() => [ALL, ...categoriesOf(partners)], [partners]);

    const visible = useMemo(
        () =>
            partners
                .filter((p) => p.status === "active")
                .filter((p) => category === ALL || p.category === category)
                .filter((p) => matchesQuery(p, query)),
        [partners, category, query],
    );

    return (
        <Page
            title="Partenaires"
            subtitle="Le réseau référencé par le Ministère du Job et Bonheur."
        >
            <div className={styles.search}>
                <Search className={styles.searchIcon} aria-hidden="true" />
                <input
                    type="search"
                    className={styles.searchInput}
                    placeholder="Rechercher un partenaire, une ville..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    aria-label="Rechercher un partenaire"
                />
            </div>

            <div className={styles.filters} role="group" aria-label="Filtrer par catégorie">
                {categories.map((name) => (
                    <button
                        key={name}
                        type="button"
                        className={
                            name === category ? `${styles.filter} ${styles.filterActive}` : styles.filter
                        }
                        aria-pressed={name === category}
                        onClick={() => setCategory(name)}
                    >
                        {name}
                    </button>
                ))}
            </div>

            {error && <p className={styles.error}>{error}</p>}

            {loading ? (
                <p className={styles.info}>Chargement du catalogue...</p>
            ) : visible.length === 0 ? (
                <div className={styles.empty}>
                    <SearchX className={styles.emptyIcon} aria-hidden="true" />
                    <p className={styles.emptyTitle}>Aucun partenaire trouvé</p>
                    <p className={styles.emptyHint}>
                        Essayez un autre mot-clé — de nouveaux partenaires sont en cours de signature.
                    </p>
                </div>
            ) : (
                <>
                    <p className={styles.count}>
                        {visible.length} partenaire{visible.length > 1 ? "s" : ""} référencé
                        {visible.length > 1 ? "s" : ""}
                    </p>

                    <ul className={styles.list}>
                        {visible.map((partner) => (
                            <PartnerCard key={partner.id} partner={partner} />
                        ))}
                    </ul>
                </>
            )}
        </Page>
    );
}
