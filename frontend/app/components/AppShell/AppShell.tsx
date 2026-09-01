"use client";

import { usePathname } from "next/navigation";
import Navbar from "../Navbar/Navbar";
import styles from "./AppShell.module.css";

const BARE_ROUTES = ["/login", "/register", "/partner", "/admin"];

export default function AppShell({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    // NOTE: « / » est comparé à l'identique — en startsWith il attraperait tout.
    const bare = pathname === "/" || BARE_ROUTES.some((route) => pathname.startsWith(route));

    if (bare) return <>{children}</>;

    return (
        <>
            <Navbar />
            <div className={styles.content}>{children}</div>
        </>
    );
}
