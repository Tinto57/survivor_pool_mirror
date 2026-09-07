"use client";

import { useEffect, useMemo, useState } from "react";
import { MousePointerClick, Send } from "lucide-react";
import Page from "../../components/Page/Page";
import AdminNav from "../../components/AdminNav/AdminNav";
import { ApiError, publishSpotlight, republishSpotlight } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import { formatDateTime, getMinisterSpotlightHistory, getPartners } from "../../lib/catalog";
import type { MinisterSpotlight, Partner } from "../../lib/catalog";
import { useAdminGuard } from "../useAdminGuard";
import styles from "./coup-de-coeur.module.css";

const MESSAGE_MAX_LENGTH = 140;

export default function MinisterSpotlightAdminPage() {
    const { admin, error: guardError } = useAdminGuard();

    const [partners, setPartners] = useState<Partner[]>([]);
    const [history, setHistory] = useState<MinisterSpotlight[]>([]);
    const [partnerId, setPartnerId] = useState<number | "">("");
    const [message, setMessage] = useState("");
    const [publishing, setPublishing] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!admin) return;

        const token = getAccessToken();

        Promise.all([getPartners(token), getMinisterSpotlightHistory(token)])
            .then(([nextPartners, nextHistory]) => {
                setPartners(nextPartners);
                setHistory(nextHistory);
            })
            .catch((err) => setError(err instanceof ApiError ? err.message : "Une erreur est survenue."));
    }, [admin]);

    const activePartners = useMemo(
        () => partners.filter((p) => p.status === "active"),
        [partners],
    );

    async function handlePublish() {
        const token = getAccessToken();
        if (!token || !partnerId || !message.trim()) return;

        setError(null);
        setPublishing(true);
        try {
            const result = await publishSpotlight(Number(partnerId), message.trim(), token);
            const partner = partners.find((p) => p.id === Number(partnerId));

            setHistory((current) => [
                {
                    id: result.id,
                    partner: result.partner,
                    message: result.message,
                    is_active: true,
                    click_count: result.click_count,
                    published_by: result.published_by,
                    published_at: result.published_at,
                },
                ...current.map((entry) => ({ ...entry, is_active: false })),
            ]);
            setNotice(`${partner?.business_name ?? "Le partenaire"} est désormais le Coup de cœur du Ministre.`);
            setPartnerId("");
            setMessage("");
        } catch (err) {
            setError(err instanceof ApiError ? err.message : "La publication a échoué.");
        } finally {
            setPublishing(false);
        }
    }

    async function handleRepublish(entry: MinisterSpotlight) {
        const token = getAccessToken();
        if (!token) return;

        setError(null);
        try {
            await republishSpotlight(entry.id, token);
            setHistory((current) =>
                current.map((e) => ({ ...e, is_active: e.id === entry.id })),
            );
            setNotice(`${entry.partner.business_name} est de nouveau en ligne.`);
        } catch (err) {
            setError(err instanceof ApiError ? err.message : "La republication a échoué.");
        }
    }

    if (guardError && !admin) return <p className={styles.error} role="alert">{guardError}</p>;

    if (!admin) {
        return (
            <Page title="Coup de cœur du Ministre" wide>
                <div className={styles.skeleton} aria-hidden="true" />
            </Page>
        );
    }

    return (
        <Page
            title="Coup de cœur du Ministre"
            subtitle="Mettez en avant un partenaire sur l'accueil salarié, en deux tapotements."
            simulation
            wide
        >
            <div className={styles.layout}>
                <AdminNav section="coup-de-coeur" />

                <div className={styles.panel}>
                    {notice && <p className={styles.notice} role="status">{notice}</p>}
                    {error && <p className={styles.error} role="alert">{error}</p>}

                    <div className={styles.form}>
                        <div className={styles.field}>
                            <label htmlFor="spotlight-partner">Partenaire à mettre en avant</label>
                            <select
                                id="spotlight-partner"
                                className={styles.select}
                                value={partnerId}
                                onChange={(e) => setPartnerId(e.target.value ? Number(e.target.value) : "")}
                            >
                                <option value="">Choisir un partenaire actif…</option>
                                {activePartners.map((partner) => (
                                    <option key={partner.id} value={partner.id}>
                                        {partner.business_name} · {partner.category}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className={styles.field}>
                            <label htmlFor="spotlight-message">Votre message (deux lignes)</label>
                            <textarea
                                id="spotlight-message"
                                className={styles.textarea}
                                rows={3}
                                maxLength={MESSAGE_MAX_LENGTH}
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Ex. : Un artisan comme on n'en fait plus, foncez-y !"
                            />
                            <span className={styles.counter}>
                                {message.length}/{MESSAGE_MAX_LENGTH}
                            </span>
                        </div>

                        <button
                            type="button"
                            className={styles.publish}
                            disabled={!partnerId || !message.trim() || publishing}
                            onClick={handlePublish}
                        >
                            <Send aria-hidden="true" />
                            {publishing ? "Publication…" : "Publier"}
                        </button>
                    </div>

                    <h2 className={styles.sectionTitle}>Historique des publications</h2>

                    {history.length === 0 ? (
                        <p className={styles.empty}>Aucune publication pour le moment.</p>
                    ) : (
                        <ul className={styles.list}>
                            {history.map((entry) => (
                                <li key={entry.id} className={styles.entry}>
                                    <div className={styles.entryBody}>
                                        <p className={styles.entryName}>{entry.partner.business_name}</p>
                                        <p className={styles.entryMessage}>{entry.message}</p>
                                        <p className={styles.entryMeta}>
                                            {entry.published_at && formatDateTime(entry.published_at)}
                                            {entry.published_by ? ` · ${entry.published_by}` : ""}
                                        </p>
                                    </div>

                                    <span className={styles.clicks}>
                                        <MousePointerClick aria-hidden="true" size={13} />
                                        {entry.click_count ?? 0}
                                    </span>

                                    {entry.is_active ? (
                                        <span className={styles.active}>En ligne</span>
                                    ) : (
                                        <button
                                            type="button"
                                            className={styles.republish}
                                            onClick={() => handleRepublish(entry)}
                                        >
                                            Republier
                                        </button>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </Page>
    );
}
