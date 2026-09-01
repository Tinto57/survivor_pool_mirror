import styles from "./Page.module.css";

type PageProps = {
    title: string;
    subtitle?: string;
    /** Contenu aligné à droite du titre (bouton retour, action...). */
    aside?: React.ReactNode;
    children: React.ReactNode;
};

/** Gabarit commun des écrans salarié : conteneur centré + en-tête. */
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
