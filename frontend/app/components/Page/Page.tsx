import styles from "./Page.module.css";

type PageProps = {
    title: string;
    subtitle?: string;
    aside?: React.ReactNode;
    children: React.ReactNode;
};

export default function Page({ title, subtitle, aside, children }: PageProps) {
    return (
        <main className={styles.page}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>{title}</h1>
                    {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
                </div>
                {aside}
            </header>

            {children}
        </main>
    );
}
