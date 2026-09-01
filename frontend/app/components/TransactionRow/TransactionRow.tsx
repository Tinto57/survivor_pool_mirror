import { ArrowDownLeft } from "lucide-react";
import Avatar from "../Avatar/Avatar";
import type { Transaction } from "../../lib/catalog";
import { formatAmount, formatDateTime } from "../../lib/catalog";
import styles from "./TransactionRow.module.css";

export default function TransactionRow({ transaction }: { transaction: Transaction }) {
    const isTopUp = transaction.kind === "topup";
    const cancelled = transaction.is_cancelled;

    const amountClass = [
        styles.amount,
        isTopUp && !cancelled ? styles.amountTopUp : "",
        cancelled ? styles.amountCancelled : "",
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <li className={styles.row}>
            <Avatar
                name={transaction.partner_name}
                size="sm"
                icon={isTopUp ? <ArrowDownLeft /> : undefined}
            />

            <div className={styles.body}>
                <p className={styles.name}>{transaction.partner_name}</p>
                <p className={styles.meta}>
                    {cancelled ? (
                        <span className={styles.cancelled}>Annulée</span>
                    ) : (
                        formatDateTime(transaction.validated_at)
                    )}
                </p>
            </div>

            <span className={amountClass}>
                {isTopUp ? "+" : "−"}
                {formatAmount(transaction.amount)}
            </span>
        </li>
    );
}
