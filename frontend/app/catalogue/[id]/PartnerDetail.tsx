"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, BadgeCheck, Heart, MapPin, Navigation } from "lucide-react";
import Avatar from "../../components/Avatar/Avatar";
import Page from "../../components/Page/Page";
import { getAccessToken } from "../../lib/auth";
import { getPartner } from "../../lib/catalog";
import type { Partner } from "../../lib/catalog";
import styles from "./partner.module.css";

export default function PartnerDetail() {
    const params = useParams();
    const id = params?.id ? String(params.id) : null;

    const [partner, setPartner] = useState<Partner | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        getPartner(Number(id), getAccessToken())
            .then(setPartner)
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) {
        return (
            <Page title="Partenaire">
                <p className={styles.info}>Chargement...</p>
            </Page>
        );
    }

    if (error || !partner) {
        return (
            <Page title="Partenaire introuvable">
                <p className={styles.info}>
                    {error ?? "Ce partenaire n'est plus référencé par le Ministère."}
                </p>
                <Link href="/catalogue" className={styles.backLink}>
                    Retour au catalogue
                </Link>
            </Page>
        );
    }

    const mapsQuery =
        partner.latitude !== null && partner.longitude !== null
            ? `${partner.latitude},${partner.longitude}`
            : partner.address;

    return (
        <main className={styles.page}>
            <Link href="/catalogue" className={styles.back} aria-label="Retour au catalogue">
                <ArrowLeft className={styles.backIcon} aria-hidden="true" />
            </Link>

            <header className={styles.hero}>
                <Avatar name={partner.business_name} size="lg" />

                <h1 className={styles.name}>{partner.business_name}</h1>
                <p className={styles.category}>
                    {partner.category} · {partner.city}
                </p>

                <div className={styles.badges}>
                    <span className={styles.official}>
                        <BadgeCheck className={styles.badgeIcon} aria-hidden="true" />
                        Partenaire Officiel du Ministère
                    </span>

                    {partner.is_featured && (
                        <span className={styles.featured}>
                            <Heart className={styles.badgeIconFilled} aria-hidden="true" />
                            Coup de cœur du Ministre
                        </span>
                    )}
                </div>
            </header>

            <section className={styles.card}>
                <h2 className={styles.cardTitle}>À propos</h2>
                <p className={styles.purpose}>{partner.business_purpose}</p>
            </section>

            <section className={styles.card}>
                <h2 className={styles.cardTitle}>Où le trouver</h2>

                <p className={styles.address}>
                    <MapPin className={styles.addressIcon} aria-hidden="true" />
                    {partner.address}
                </p>
            </section>

            <a
                className={styles.cta}
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapsQuery)}`}
                target="_blank"
                rel="noopener noreferrer"
            >
                <Navigation className={styles.ctaIcon} aria-hidden="true" />
                Ouvrir l&apos;itinéraire
            </a>

            <p className={styles.footnote}>
                Réglez sur place avec votre solde Ticket Tout — le paiement par QR code arrive
                très bientôt.
            </p>
        </main>
    );
}
