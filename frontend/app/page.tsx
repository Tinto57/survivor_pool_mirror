"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "./lib/api";
import {
    getAccessToken,
    getCurrentRole,
    getCurrentUserId,
    homePathForRole,
    logout,
    storeRole,
} from "./lib/auth";

/**
 * Racine du site : simple aiguillage vers l'espace du rôle connecté.
 *
 * Chaque espace a désormais son URL (/employee, /partner, /admin) ; « / » ne
 * fait que rediriger, et renvoie sur la connexion si personne n'est identifié.
 */
export default function RootRedirect() {
    const router = useRouter();

    useEffect(() => {
        const token = getAccessToken();
        const userId = getCurrentUserId();

        if (!token || userId === null) {
            router.replace("/login");
            return;
        }

        const role = getCurrentRole();

        if (role) {
            router.replace(homePathForRole(role));
            return;
        }

        // NOTE: session ouverte avant que le rôle ne soit stocké — on le relit.
        getUser(userId, token)
            .then((user) => {
                storeRole(user.role);
                router.replace(homePathForRole(user.role));
            })
            .catch(() => {
                logout();
                router.replace("/login");
            });
    }, [router]);

    return null;
}
