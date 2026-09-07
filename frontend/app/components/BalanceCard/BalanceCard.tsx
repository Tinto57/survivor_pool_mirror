import type { Balance } from "../../lib/catalog";
import { formatAmount, splitAmount } from "../../lib/catalog";
import FakeQrCode from "../FakeQrCode/FakeQrCode";
import SimulationBadge from "../SimulationBadge/SimulationBadge";
import styles from "./BalanceCard.module.css";

export default function BalanceCard({ balance }: { balance: Balance }) {
    const { integer, cents } = splitAmount(balance.amount);
    const empty = balance.amount <= 0;

    return (
        <section className={styles.card}>
            <div className={styles.labelRow}>
                <p className={styles.label}>Solde Ticket Tout</p>
                <SimulationBadge />
            </div>

            <p className={styles.amount}>
                {integer}
                <span className={styles.cents}>{cents}</span>
            </p>

            <p className={styles.tagline}>
                {empty
                    ? "Votre prochain abondement arrive bientôt, gardez le sourire !"
                    : "à dépenser chez vos partenaires préférés !"}
            </p>

            <FakeQrCode />

            <dl className={styles.stats}>
                <div className={styles.stat}>
                    <dt className={styles.statLabel}>
                        Crédité ce mois-ci <SimulationBadge size="sm" />
                    </dt>
                    <dd className={`${styles.statValue} ${styles.statIn}`}>
                        {formatAmount(balance.topped_up_this_month)}
                    </dd>
                </div>

                <div className={styles.stat}>
                    <dt className={styles.statLabel}>
                        Dépensé ce mois-ci <SimulationBadge size="sm" />
                    </dt>
                    <dd className={styles.statValue}>{formatAmount(balance.spent_this_month)}</dd>
                </div>
            </dl>

            <p className={styles.employer}>Abondé par {balance.employer}</p>
        </section>
    );
}
