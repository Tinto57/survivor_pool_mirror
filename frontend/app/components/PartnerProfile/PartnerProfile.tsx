import { BadgeCheck, Heart} from "lucide-react";
import Avatar from "../Avatar/Avatar";
import type { Partner } from "../../lib/catalog";
import styles from "./PartnerProfile.module.css";    
    
export default function PartnerProfile({ partner }: { partner: Partner }) {
    return (
        <header className={styles.hero}>
            <Avatar name={partner.business_name} size="lg" />

            <h1 className={styles.name}>{partner.business_name}</h1>
            <p className={styles.category}>
                {partner.category} · {partner.city}
            </p>

            <div className={styles.badges}>
                <span className={styles.official}>
                    <BadgeCheck className={styles.badgeIcon} aria-hidden="true" />
                    Partenaire Officiel du Ministère
                </span>

                {partner.is_featured && (
                    <span className={styles.featured}>
                        <Heart className={styles.badgeIconFilled} aria-hidden="true" />
                        Coup de cœur du Ministre
                    </span>
                )}
            </div>
        </header>
    );
}