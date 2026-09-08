import Link from "next/link";
import { ChevronRight } from "lucide-react";
import Avatar from "../Avatar/Avatar";
import type { Partner } from "../../lib/catalog";
import styles from "./PartnerCard.module.css";

export default function PartnerCard({ partner }: { partner: Partner }) {
    return (
        <li>
            <Link href={`/catalogue/${partner.id}`} className={styles.row}>
                <Avatar name={partner.business_name} />

                <div className={styles.body}>
                    <p className={styles.name}>{partner.business_name}</p>
                    <p className={styles.meta}>
                        {partner.category} · {partner.city}
                    </p>
                </div>

                <ChevronRight className={styles.chevron} aria-hidden="true" />
            </Link>
        </li>
    );
}
