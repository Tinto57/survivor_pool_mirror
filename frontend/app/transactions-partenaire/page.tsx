"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import Page from "../components/Page/Page";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import { getAccessToken } from "../lib/auth";
import { formatAmount, formatDateTime, getTransactions } from "../lib/catalog";
import type { Transaction } from "../lib/catalog";
import styles from "./page.module.css";

export default function TransactionsPartenairePage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
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

    const totalEncaisse = useMemo(
        () =>
            transactions
                .filter((t) => t.transaction_type === "PAYMENT" && !t.is_cancelled)
                .reduce((sum, t) => sum + t.amount, 0),
        [transactions],
    );

    return (
        <Page
            title="Historique des transactions"
            subtitle="Les paiements encaissés auprès des salariés CartePro."
            simulation
            wide
            aside={
                <Link href="/partner" className={styles.backLink}>
                    <ArrowLeft aria-hidden="true" size={16} />
                    Retour
                </Link>
            }
        >
            {error && <p className={styles.errorMessage} role="alert">{error}</p>}

            <section className={styles.summary} aria-label="Résumé des transactions">
                <div className={styles.summaryCard}>
                    <p className={styles.summaryLabel}>
                        Transactions <SimulationBadge size="sm" />
                    </p>
                    <p className={styles.summaryValue}>{transactions.length}</p>
                </div>

                <div className={styles.summaryCard}>
                    <p className={styles.summaryLabel}>
                        Total encaissé <SimulationBadge size="sm" />
                    </p>
                    <p className={styles.summaryValue}>{formatAmount(totalEncaisse)}</p>
                </div>
            </section>

            {loading ? (
                <p className={styles.info}>Chargement...</p>
            ) : transactions.length === 0 ? (
                <div className={styles.empty}>
                    <p className={styles.emptyTitle}>Aucune transaction</p>
                    <p className={styles.emptyHint}>
                        Les paiements que vous encaissez apparaîtront ici.
                    </p>
                </div>
            ) : (
                <section className={styles.tableWrap} aria-label="Liste des transactions">
                    <table className={styles.table}>
                        <thead className={styles.thead}>
                            <tr>
                                <th className={styles.th}>Date</th>
                                <th className={styles.th}>Type</th>
                                <th className={styles.th}>Montant</th>
                                <th className={styles.th}>Statut</th>
                                <th className={styles.th}>Référence</th>
                            </tr>
                        </thead>

                        <tbody>
                            {transactions.map((transaction, index) => (
                                <tr
                                    key={transaction.id}
                                    className={index % 2 === 0 ? styles.row : styles.rowAlt}
                                >
                                    <td className={styles.td}>{formatDateTime(transaction.validated_at)}</td>
                                    <td className={styles.td}>
                                        {transaction.transaction_type === "PAYMENT" ? "Paiement" : "Contre-écriture"}
                                    </td>
                                    <td className={styles.tdStrong}>{formatAmount(transaction.amount)}</td>
                                    <td className={styles.td}>
                                        <span
                                            className={
                                                transaction.is_cancelled ? styles.statusCancelled : styles.statusOk
                                            }
                                        >
                                            {transaction.is_cancelled ? "Annulée" : "Validée"}
                                        </span>
                                    </td>
                                    <td className={styles.tdCode}>#{transaction.id}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </section>
            )}
        </Page>
    );
}
