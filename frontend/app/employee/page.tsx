"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import BalanceCard from "../components/BalanceCard/BalanceCard";
import PartnerTile from "../components/PartnerTile/PartnerTile";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import TransactionRow from "../components/TransactionRow/TransactionRow";
import { getAccessToken } from "../lib/auth";
import { getBalance, getPartners, getTransactions } from "../lib/catalog";
import type { Balance, Partner, Transaction } from "../lib/catalog";
import styles from "./employee.module.css";

export default function Home() {
    const [balance, setBalance] = useState<Balance | null>(null);
    const [partners, setPartners] = useState<Partner[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = getAccessToken();

        Promise.all([getBalance(token), getPartners(token), getTransactions(token)])
            .then(([nextBalance, nextPartners, nextTransactions]) => {
                setBalance(nextBalance);
                setPartners(nextPartners);
                setTransactions(nextTransactions);
            })
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, []);

    const featured = partners.filter((p) => p.is_featured && p.status === "active");
    const recent = transactions.slice(0, 4);

    return (
        <main className={styles.page}>
            <header className={styles.topbar}>
                <span className={styles.brand}>Ticket Tout</span>
                <SimulationBadge size="sm" />
            </header>

            {error && <p className={styles.error}>{error}</p>}

            {loading ? (
                <div className={styles.skeleton} aria-hidden="true" />
            ) : (
                balance && <BalanceCard balance={balance} />
            )}

            {featured.length > 0 && (
                <section className={styles.section}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>Coup de cœur du Ministre</h2>
                        <Link href="/catalogue" className={styles.sectionLink}>
                            Tout voir
                        </Link>
                    </div>

                    <div className={styles.carousel}>
                        {featured.map((partner) => (
                            <PartnerTile key={partner.id} partner={partner} />
                        ))}
                    </div>
                </section>
            )}

            {recent.length > 0 && (
                <section className={styles.section}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>Récemment</h2>
                        <Link href="/historique" className={styles.sectionLink}>
                            Tout voir
                        </Link>
                    </div>

                    <ul className={styles.list}>
                        {recent.map((transaction) => (
                            <TransactionRow key={transaction.id} transaction={transaction} />
                        ))}
                    </ul>
                </section>
            )}
        </main>
    );
}
