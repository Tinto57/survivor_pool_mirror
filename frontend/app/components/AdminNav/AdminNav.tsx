"use client";

import Link from "next/link";
import styles from "./AdminNav.module.css";

export type DashboardTab = "requests" | "partners" | "employees" | "journal";

const DASHBOARD_TABS: { id: DashboardTab; label: string }[] = [
    { id: "requests", label: "Demandes" },
    { id: "partners", label: "Partenaires" },
    { id: "employees", label: "Salariés" },
    { id: "journal", label: "Journal" },
];

type AdminNavProps = {
    /** Espace affiché : le pilotage bascule en liens quand on est ailleurs. */
    section: "dashboard" | "registre";
    activeTab?: DashboardTab;
    onSelectTab?: (tab: DashboardTab) => void;
    pendingCount?: number;
};

export default function AdminNav({
    section,
    activeTab,
    onSelectTab,
    pendingCount = 0,
}: AdminNavProps) {
    const onDashboard = section === "dashboard";

    return (
        <nav className={styles.nav} aria-label="Sections de l'espace Ministère">
            <p className={styles.group}>Pilotage</p>

            {DASHBOARD_TABS.map(({ id, label }) => {
                const badge =
                    id === "requests" && pendingCount > 0 ? (
                        <span className={styles.count}>{pendingCount}</span>
                    ) : null;

                // Hors du tableau de bord, ces entrées y ramènent par un lien.
                if (!onDashboard) {
                    return (
                        <Link key={id} href="/admin" className={styles.item}>
                            {label}
                        </Link>
                    );
                }

                return (
                    <button
                        key={id}
                        type="button"
                        className={
                            id === activeTab ? `${styles.item} ${styles.itemActive}` : styles.item
                        }
                        aria-pressed={id === activeTab}
                        onClick={() => onSelectTab?.(id)}
                    >
                        {label}
                        {badge}
                    </button>
                );
            })}

            <p className={styles.group}>Conformité</p>

            <Link
                href="/admin/registre"
                className={
                    section === "registre" ? `${styles.item} ${styles.itemActive}` : styles.item
                }
                aria-current={section === "registre" ? "page" : undefined}
            >
                Registre RGPD
            </Link>
        </nav>
    );
}
