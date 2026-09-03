import Image from "next/image";
import styles from "./BlocMarque.module.css";

export default function BlocMarque({ size = "md" }: { size?: "sm" | "md" }) {
    return (
        <span className={size === "sm" ? `${styles.wrap} ${styles.sm}` : styles.wrap}>
            <Image
                src="/bloque-marque.png"
                alt="République Française — Liberté, Égalité, Fraternité"
                width={470}
                height={425}
                className={styles.image}
                priority
            />
        </span>
    );
}
