import styles from "./SimulationBadge.module.css";

export default function SimulationBadge({ size = "md" }: { size?: "sm" | "md" }) {
    return (
        <span className={size === "sm" ? `${styles.badge} ${styles.sm}` : styles.badge}>
            Simulation
        </span>
    );
}
