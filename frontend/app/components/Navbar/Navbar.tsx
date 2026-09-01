"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Navbar.module.css";

import { House, History, Settings, Store } from "lucide-react";

const LINKS = [
    { href: "/employee", label: "Accueil", Icon: House },
    { href: "/catalogue", label: "Partenaires", Icon: Store },
    { href: "/historique", label: "Historique", Icon: History },
    { href: "/reglages", label: "Réglages", Icon: Settings },
];

export default function Navbar() {
    const pathname = usePathname();

    function isActive(href: string): boolean {
        return pathname === href || pathname.startsWith(`${href}/`);
    }

    return (
        <nav className={styles.navbar}>
            <Link href="/employee" className={styles.logo}>
                <span>Ticket Tout</span>
            </Link>

            <div className={styles.links}>
                {LINKS.map(({ href, label, Icon }) => (
                    <Link
                        key={href}
                        href={href}
                        className={isActive(href) ? `${styles.link} ${styles.linkActive}` : styles.link}
                        aria-current={isActive(href) ? "page" : undefined}
                    >
                        <Icon className={styles.icon} aria-hidden="true" />
                        <span>{label}</span>
                    </Link>
                ))}
            </div>
        </nav>
    );
}
