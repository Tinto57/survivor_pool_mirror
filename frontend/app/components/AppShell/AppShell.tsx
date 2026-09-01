"use client";

import { usePathname } from "next/navigation";
import Navbar from "../Navbar/Navbar";
import styles from "./AppShell.module.css";

/**
 * Routes affichées sans la barre de navigation salarié : écrans de connexion,
 * et espaces partenaire / admin qui auront la leur.
 */
const BARE_ROUTES = ["/login", "/register", "/partner", "/admin"];

export default function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    // NOTE: « / » est comparé à l'identique — en startsWith il attraperait tout.
    const bare = pathname === "/" || BARE_ROUTES.some((route) => pathname.startsWith(route));

    if (bare) return <>{children}</>;

    return (
        <>
            <Navbar />
            {/* Le padding dégage la barre d'onglets fixe en bas sur mobile. */}
            <div className={styles.content}>{children}</div>
        </>
    );
}
