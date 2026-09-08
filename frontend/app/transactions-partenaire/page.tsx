"use client";

import Page from "../components/Page/Page";
import styles from "./page.module.css";

type PartnerTransaction = {
    id: string;
    date: string;
    employee: string;
    amount: number;
    status: "Validée" | "Annulée";
};

const PREVIEW_TRANSACTIONS: PartnerTransaction[] = [
    {
        id: "TTX-2026-0907-001",
        date: "2026-09-07T09:12:00",
        employee: "Camille Bernard",
        amount: 24.50,
        status: "Validée",
    },
    {
        id: "TTX-2026-0907-002",
        date: "2026-09-07T10:41:00",
        employee: "Nina Laurent",
        amount: 12.00,
        status: "Validée",
    },
    {
        id: "TTX-2026-0907-003",
        date: "2026-09-07T11:18:00",
        employee: "Lucas Martin",
        amount: 38.20,
        status: "Annulée",
    },
    {
        id: "TTX-2026-0907-004",
        date: "2026-09-07T13:05:00",
        employee: "Sarah Petit",
        amount: 18.90,
        status: "Validée",
    },
];

const euro = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
});

function formatDateTime(value: string): string {
    return new Date(value).toLocaleString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export default function TransactionsPartenairePreviewPage() {
    const totalValidated = PREVIEW_TRANSACTIONS.filter((t) => t.status === "Validée").reduce(
        (sum, t) => sum + t.amount,
        0,
    );

    return (
        <Page
            title="Historique des transactions partenaire"
            subtitle="Page de prévisualisation locale (non reliée). Modifie librement les données ici pour préparer la suite."
            wide
        >
            <section className={styles.summary} aria-label="Résumé des transactions">
                <div className={styles.summaryCard}>
                    <p className={styles.summaryLabel}>Transactions</p>
                    <p className={styles.summaryValue}>{PREVIEW_TRANSACTIONS.length}</p>
                </div>

                <div className={styles.summaryCard}>
                    <p className={styles.summaryLabel}>Total encaissé</p>
                    <p className={styles.summaryValue}>{euro.format(totalValidated)}</p>
                </div>
            </section>

            <section className={styles.tableWrap} aria-label="Liste des transactions">
                <table className={styles.table}>
                    <thead className={styles.thead}>
                        <tr>
                            <th className={styles.th}>Date</th>
                            <th className={styles.th}>Salarié</th>
                            <th className={styles.th}>Montant</th>
                            <th className={styles.th}>Statut</th>
                            <th className={styles.th}>Référence</th>
                        </tr>
                    </thead>

                    <tbody>
                        {PREVIEW_TRANSACTIONS.map((transaction, index) => (
                            <tr
                                key={transaction.id}
                                className={index % 2 === 0 ? styles.row : styles.rowAlt}
                            >
                                <td className={styles.td}>{formatDateTime(transaction.date)}</td>
                                <td className={styles.td}>{transaction.employee}</td>
                                <td className={styles.tdStrong}>{euro.format(transaction.amount)}</td>
                                <td className={styles.td}>
                                    <span
                                        className={
                                            transaction.status === "Validée"
                                                ? styles.statusOk
                                                : styles.statusCancelled
                                        }
                                    >
                                        {transaction.status}
                                    </span>
                                </td>
                                <td className={styles.tdCode}>{transaction.id}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </section>
        </Page>
    );
}
