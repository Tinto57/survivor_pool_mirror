"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, getUser } from "../lib/api";
import type { ApiUser } from "../lib/api";
import { getAccessToken, getCurrentUserId, homePathForRole, logout } from "../lib/auth";

/**
 * Vérifie que la session en cours est bien celle d'un administrateur.
 *
 * Le profil est relu côté serveur : un jeton expiré ou un rôle qui ne
 * correspond pas renvoie ailleurs au lieu d'afficher un faux « connecté ».
 */
export function useAdminGuard() {
    const router = useRouter();
    const [admin, setAdmin] = useState<ApiUser | null>(null);
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
                if (profile.role !== "admin") {
                    router.replace(homePathForRole(profile.role));
                    return;
                }

                setAdmin(profile);
            })
            .catch((err) => {
                if (err instanceof ApiError && err.status === 401) {
                    logout();
                    router.replace("/login");
                    return;
                }

                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            });
    }, [router]);

    return { admin, error };
}
