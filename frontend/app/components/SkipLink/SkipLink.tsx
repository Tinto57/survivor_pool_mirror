/** RGAA 12.7 : lien d'évitement, premier élément focusable de chaque page. */
export default function SkipLink() {
    return (
        <a href="#main-content" className="skip-link">
            Aller au contenu
        </a>
    );
}
