import Link from "next/link";
import Avatar from "../Avatar/Avatar";
import type { Partner } from "../../lib/catalog";
import styles from "./PartnerTile.module.css";

export default function PartnerTile({ partner }: { partner: Partner }) {
    return (
        <Link href={`/catalogue/${partner.id}`} className={styles.tile}>
            <Avatar name={partner.business_name} />

            <p className={styles.name}>{partner.business_name}</p>
            <p className={styles.purpose}>{partner.business_purpose}</p>

            <span className={styles.category}>{partner.category}</span>
        </Link>
    );
}
