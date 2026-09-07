import { Landmark, MapPin } from "lucide-react";
import Avatar from "../Avatar/Avatar";
import type { MinisterSpotlight } from "../../lib/catalog";
import styles from "../../coup-de-coeur/coup-de-coeur.module.css";

/** Fiche complète d'un Coup de cœur du Ministre : partenaire, message, adresse, itinéraire. */
export default function MinisterSpotlightDetail({ spotlight }: { spotlight: MinisterSpotlight }) {
    const mapsQuery = spotlight.partner.address;

    return (
        <>
            <div className={styles.hero}>
                <Avatar name={spotlight.partner.business_name} size="lg" />

                <p className={styles.kicker}>
                    <Landmark className={styles.kickerIcon} aria-hidden="true" />
                    Coup de cœur du Ministre
                </p>

                <h1 className={styles.name}>{spotlight.partner.business_name}</h1>
                <p className={styles.category}>{spotlight.partner.category}</p>
            </div>

            <section className={styles.card}>
                <h2 className={styles.cardTitle}>Le mot du Ministre</h2>
                <p className={styles.message}>« {spotlight.message} »</p>
                <p className={styles.signature}>— Jean-Eudes Berlier, Ministre du Job et Bonheur</p>
            </section>

            <section className={styles.card}>
                <h2 className={styles.cardTitle}>Où le trouver</h2>
                <p className={styles.address}>
                    <MapPin className={styles.addressIcon} aria-hidden="true" />
                    {spotlight.partner.address}
                </p>
            </section>

            <a
                className={styles.cta}
                href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapsQuery)}`}
                target="_blank"
                rel="noopener noreferrer"
            >
                Ouvrir l&apos;itinéraire
            </a>
        </>
    );
}
