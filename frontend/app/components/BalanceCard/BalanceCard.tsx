import Link from "next/link";
import { History, QrCode, Store } from "lucide-react";
import type { Balance } from "../../lib/catalog";
import { formatAmount, splitAmount } from "../../lib/catalog";
import styles from "./BalanceCard.module.css";

/**
 * Écran de solde, construit comme la page d'accueil d'une application bancaire :
 * un montant en très gros caractères, puis une rangée d'actions rondes.
 *
 * Le cahier des charges insiste sur le ton : on n'annonce pas un « restant »
 * mais bien un montant « à dépenser chez vos partenaires préférés ».
 */
export default function BalanceCard({ balance }: { balance: Balance }) {
    const { integer, cents } = splitAmount(balance.amount);
    const empty = balance.amount <= 0;

    return (
        <section className={styles.card}>
            <p className={styles.label}>Solde Ticket Tout</p>

            <p className={styles.amount}>
                {integer}
                <span className={styles.cents}>{cents}</span>
            </p>

            <p className={styles.tagline}>
                {empty
                    ? "Votre prochain abondement arrive bientôt, gardez le sourire !"
                    : "à dépenser chez vos partenaires préférés !"}
            </p>

            <div className={styles.actions}>
                {/* NOTE: le paiement par QR code arrive dans un second temps. */}
                <div className={`${styles.action} ${styles.actionDisabled}`}>
                    <span className={styles.actionCircle}>
                        <QrCode className={styles.actionIcon} aria-hidden="true" />
                    </span>
                    <span className={styles.actionLabel}>Payer</span>
                    <span className={styles.soon}>Bientôt</span>
                </div>

                <Link href="/catalogue" className={styles.action}>
                    <span className={styles.actionCircle}>
                        <Store className={styles.actionIcon} aria-hidden="true" />
                    </span>
                    <span className={styles.actionLabel}>Partenaires</span>
                </Link>

                <Link href="/historique" className={styles.action}>
                    <span className={styles.actionCircle}>
                        <History className={styles.actionIcon} aria-hidden="true" />
                    </span>
                    <span className={styles.actionLabel}>Historique</span>
                </Link>
            </div>

            <dl className={styles.stats}>
                <div className={styles.stat}>
                    <dt className={styles.statLabel}>Crédité ce mois-ci</dt>
                    <dd className={`${styles.statValue} ${styles.statIn}`}>
                        {formatAmount(balance.topped_up_this_month)}
                    </dd>
                </div>

                <div className={styles.stat}>
                    <dt className={styles.statLabel}>Dépensé ce mois-ci</dt>
                    <dd className={styles.statValue}>{formatAmount(balance.spent_this_month)}</dd>
                </div>
            </dl>

            <p className={styles.employer}>Abondé par {balance.employer}</p>
        </section>
    );
}
