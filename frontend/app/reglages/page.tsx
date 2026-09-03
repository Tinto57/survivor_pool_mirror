"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { IdCard, LogOut, ShieldCheck } from "lucide-react";
import Avatar from "../components/Avatar/Avatar";
import BlocMarque from "../components/BlocMarque/BlocMarque";
import Page from "../components/Page/Page";
import { ApiError, getUser } from "../lib/api";
import type { ApiUser } from "../lib/api";
import { getAccessToken, getCurrentUserId, logout, ROLE_LABEL } from "../lib/auth";
import styles from "./reglages.module.css";

export default function ReglagesPage() {
    const router = useRouter();
    const [user, setUser] = useState<ApiUser | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const token = getAccessToken();
        const userId = getCurrentUserId();

        if (!token || userId === null) {
            router.replace("/login");
            return;
        }

        getUser(userId, token)
            .then(({ user: profile }) => setUser(profile))
            .catch((err) => {
                if (err instanceof ApiError && err.status === 401) {
                    logout();
                    router.replace("/login");
                    return;
                }

                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            });
    }, [router]);

    function handleLogout() {
        logout();
        router.replace("/login");
    }

    const fullName = user ? [user.first_name, user.last_name].filter(Boolean).join(" ") : "";
    const displayName = fullName || user?.username || "";
    const roleLabel = user ? ROLE_LABEL[user.role] : undefined;

    return (
        <Page title="Réglages">
            {error && <p className={styles.error}>{error}</p>}

            {!user && !error ? (
                <div className={styles.skeleton} aria-hidden="true" />
            ) : (
                user && (
                    <>
                        <header className={styles.profile}>
                            <Avatar name={displayName} size="lg" />

                            <p className={styles.name}>{displayName}</p>
                            {roleLabel && <span className={styles.role}>{roleLabel}</span>}
                        </header>

                        <h2 className={styles.sectionTitle}>Compte</h2>

                        <ul className={styles.list}>
                            <li className={styles.row}>
                                <IdCard className={styles.rowIcon} aria-hidden="true" />
                                <span className={styles.rowLabel}>Identifiant</span>
                                <span className={styles.rowValue}>{user.username}</span>
                            </li>

                            {roleLabel && (
                                <li className={styles.row}>
                                    <ShieldCheck className={styles.rowIcon} aria-hidden="true" />
                                    <span className={styles.rowLabel}>Espace</span>
                                    <span className={styles.rowValue}>{roleLabel}</span>
                                </li>
                            )}
                        </ul>

                        <button type="button" className={styles.logout} onClick={handleLogout}>
                            <LogOut className={styles.logoutIcon} aria-hidden="true" />
                            Se déconnecter
                        </button>

                        <div className={styles.blocMarque}>
                            <BlocMarque />
                        </div>
                    </>
                )
            )}
        </Page>
    );
}
