"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BadgeCheck, LogOut } from "lucide-react";
import { ApiError, getUser } from "../../lib/api";
import type { ApiUser, Role } from "../../lib/api";
import { getAccessToken, getCurrentUserId, homePathForRole, logout, ROLE_LABEL } from "../../lib/auth";
import styles from "./SessionNotice.module.css";

type SessionNoticeProps = {
    /** Rôle attendu sur cette route : on renvoie ailleurs si la session ne correspond pas. */
    role: Role;
};

/**
 * Écran d'attente des espaces partenaire et admin.
 *
 * Il ne fait rien d'autre que confirmer la session — mais il la confirme
 * vraiment : le profil est relu via /api/users/{id}, donc un token expiré ou
 * absent renvoie sur la page de connexion au lieu d'afficher un faux « connecté ».
 */
export default function SessionNotice({ role }: SessionNoticeProps) {
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
            .then((profile) => {
                // NOTE: chacun chez soi — un partenaire n'a rien à faire sur /admin.
                if (profile.role !== role) {
                    router.replace(homePathForRole(profile.role));
                    return;
                }

                setUser(profile);
            })
            .catch((err) => {
                if (err instanceof ApiError && err.status === 401) {
                    logout();
                    router.replace("/login");
                    return;
                }

                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            });
    }, [role, router]);

    function handleLogout() {
        logout();
        router.replace("/login");
    }

    if (error) return <p className={styles.error}>{error}</p>;

    if (!user) return <div className={styles.skeleton} aria-hidden="true" />;

    const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ");

    return (
        <section className={styles.card}>
            <BadgeCheck className={styles.icon} aria-hidden="true" />

            <p className={styles.lead}>
                Vous êtes bien connecté en tant que{" "}
                <strong>{ROLE_LABEL[user.role]}</strong>.
            </p>

            <dl className={styles.details}>
                {fullName && (
                    <div className={styles.detail}>
                        <dt>Nom</dt>
                        <dd>{fullName}</dd>
                    </div>
                )}
                <div className={styles.detail}>
                    <dt>Identifiant</dt>
                    <dd>{user.username}</dd>
                </div>
            </dl>

            <p className={styles.note}>
                L&apos;espace {ROLE_LABEL[user.role].toLowerCase()} n&apos;est pas encore
                construit — cette page confirme seulement que l&apos;authentification
                fonctionne de bout en bout.
            </p>

            <button type="button" className={styles.logout} onClick={handleLogout}>
                <LogOut aria-hidden="true" />
                Se déconnecter
            </button>
        </section>
    );
}
