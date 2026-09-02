import SimulationBadge from "../SimulationBadge/SimulationBadge";
import styles from "./Page.module.css";

type PageProps = {
    title: string;
    subtitle?: string;
    aside?: React.ReactNode;
    children: React.ReactNode;
    simulation?: boolean;
};

export default function Page({ title, subtitle, aside, children, simulation }: PageProps) {
    return (
        <main className={styles.page}>
            <header className={styles.header}>
                <div>
                    <div className={styles.titleRow}>
                        <h1 className={styles.title}>{title}</h1>
                        {simulation && <SimulationBadge />}
                    </div>
                    {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
                </div>
                {aside}
            </header>

            {children}
        </main>
    );
}
