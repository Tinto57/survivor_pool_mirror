"use client";

import { useEffect, useMemo, useState } from "react";
import { Receipt } from "lucide-react";
import Page from "../components/Page/Page";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import TransactionRow from "../components/TransactionRow/TransactionRow";
import { getAccessToken } from "../lib/auth";
import { formatAmount, getTransactions, monthLabel } from "../lib/catalog";
import type { Transaction } from "../lib/catalog";
import styles from "./historique.module.css";

type Filter = "all" | "PAYMENT" | "ABONDMENT";

const FILTERS: { id: Filter; label: string }[] = [
    { id: "all", label: "Tout" },
    { id: "PAYMENT", label: "Dépenses" },
    { id: "ABONDMENT", label: "Abondements" },
];

function groupByMonth(transactions: Transaction[]): [string, Transaction[]][] {
    const groups = new Map<string, Transaction[]>();

    for (const transaction of transactions) {
        const key = monthLabel(transaction.validated_at);
        const group = groups.get(key);

        if (group) group.push(transaction);
        else groups.set(key, [transaction]);
    }

    return [...groups.entries()];
}

export default function HistoriquePage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [filter, setFilter] = useState<Filter>("all");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getTransactions(getAccessToken())
            .then((data) =>
                setTransactions(
                    [...data].sort(
                        (a, b) => Date.parse(b.validated_at) - Date.parse(a.validated_at),
                    ),
                ),
            )
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, []);

    const visible = useMemo(
        () => transactions.filter((t) => filter === "all" || t.transaction_type === filter),
        [transactions, filter],
    );

    const groups = useMemo(() => groupByMonth(visible), [visible]);

    const totals = useMemo(() => {
        return {
            spent: transactions
                .filter((t) => t.transaction_type === "PAYMENT")
                .reduce((sum, t) => sum + t.amount, 0),
            received: transactions
                .filter((t) => t.transaction_type === "ABONDMENT")
                .reduce((sum, t) => sum + t.amount, 0),
        };
    }, [transactions]);

    return (
        <Page
            title="Historique"
            subtitle="Toutes vos opérations Ticket Tout, du plus récent au plus ancien."
            simulation
        >
            <div className={styles.totals}>
                <div className={styles.total}>
                    <p className={styles.totalLabel}>
                        Reçu au total <SimulationBadge size="sm" />
                    </p>
                    <p className={`${styles.totalValue} ${styles.totalIn}`}>
                        {formatAmount(totals.received)}
                    </p>
                </div>

                <div className={styles.total}>
                    <p className={styles.totalLabel}>
                        Dépensé au total <SimulationBadge size="sm" />
                    </p>
                    <p className={styles.totalValue}>{formatAmount(totals.spent)}</p>
                </div>
            </div>

            <div className={styles.filters} role="group" aria-label="Filtrer les opérations">
                {FILTERS.map(({ id, label }) => (
                    <button
                        key={id}
                        type="button"
                        className={id === filter ? `${styles.filter} ${styles.filterActive}` : styles.filter}
                        aria-pressed={id === filter}
                        onClick={() => setFilter(id)}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {error && <p className={styles.error}>{error}</p>}

            {loading ? (
                <p className={styles.info}>Chargement de l&apos;historique...</p>
            ) : groups.length === 0 ? (
                <div className={styles.empty}>
                    <Receipt className={styles.emptyIcon} aria-hidden="true" />
                    <p className={styles.emptyTitle}>Aucune opération</p>
                    <p className={styles.emptyHint}>
                        Vos paiements chez les partenaires apparaîtront ici.
                    </p>
                </div>
            ) : (
                groups.map(([month, items]) => (
                    <section key={month} className={styles.group}>
                        <h2 className={styles.groupTitle}>{month}</h2>

                        <ul className={styles.list}>
                            {items.map((transaction) => (
                                <TransactionRow key={transaction.id} transaction={transaction} />
                            ))}
                        </ul>
                    </section>
                ))
            )}
        </Page>
    );
}
