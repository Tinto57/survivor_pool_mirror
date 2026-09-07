"use client";

import { useState } from "react";
import Page from "../components/Page/Page";
import PartnerProfile from "../components/PartnerProfile/PartnerProfile";
import { getAccessToken, getCurrentUserId } from "../lib/auth";
import { getPartner } from "../lib/catalog";
import type { Partner } from "../lib/catalog";
import styles from "./partner.module.css";

export default function PartnerHome() {
    const [partner, setPartner] = useState<Partner | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const userId = getCurrentUserId();

    getPartner(Number(userId), getAccessToken())
        .then(setPartner)
        .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
        .finally(() => setLoading(false));

    if (loading) {
        return (
            <Page title="Partenaire">
                <p className={styles.info}>Chargement...</p>
            </Page>
        );
    }

    if (error || !partner) {
        return (
            <Page title="Erreur">
                <p className={styles.info}>
                    {error ?? "Une erreur est survenue lors du chargement de votre profil"}
                </p>
            </Page>
        );
    }

    return (
        <main className={styles.page}>
            <PartnerProfile partner={partner}/>
        </main>

    );
}
