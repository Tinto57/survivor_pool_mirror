import Link from "next/link";
import { ChevronRight, Landmark } from "lucide-react";
import Avatar from "../Avatar/Avatar";
import type { MinisterSpotlight as MinisterSpotlightType } from "../../lib/catalog";
import { postSpotlightClick } from "../../lib/api";
import styles from "./MinisterSpotlight.module.css";

export default function MinisterSpotlight({ spotlight }: { spotlight: MinisterSpotlightType }) {
    return (
        <Link
            href={`/catalogue/${spotlight.partner.id}`}
            className={styles.card}
            onClick={() => postSpotlightClick()}
        >
            <Avatar name={spotlight.partner.business_name} />

            <div className={styles.body}>
                <p className={styles.kicker}>
                    <Landmark className={styles.kickerIcon} aria-hidden="true" />
                    Coup de cœur du Ministre
                </p>
                <p className={styles.name}>{spotlight.partner.business_name}</p>
                <p className={styles.message}>{spotlight.message}</p>
            </div>

            <ChevronRight className={styles.chevron} aria-hidden="true" />
        </Link>
    );
}
