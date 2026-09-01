import { initialsOf, tintOf } from "../../lib/catalog";
import styles from "./Avatar.module.css";

type AvatarProps = {
    /** Sert à la fois de source du monogramme et de graine pour la couleur. */
    name: string;
    size?: "sm" | "md" | "lg";
    /** Remplace le monogramme, pour les lignes qui ne désignent pas un partenaire. */
    icon?: React.ReactNode;
};

/**
 * Pastille ronde d'un partenaire : monogramme sur aplat teinté, à la façon
 * d'un avatar marchand sans logo.
 */
export default function Avatar({ name, size = "md", icon }: AvatarProps) {
    const className = [
        styles.avatar,
        styles[size],
        icon ? styles.neutral : styles[tintOf(name)],
    ].join(" ");

    return (
        <span className={className} aria-hidden="true">
            {icon ?? initialsOf(name)}
        </span>
    );
}
