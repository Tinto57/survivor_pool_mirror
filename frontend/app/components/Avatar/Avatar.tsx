import { initialsOf, tintOf } from "../../lib/catalog";
import styles from "./Avatar.module.css";

type AvatarProps = {
    name: string;
    size?: "sm" | "md" | "lg";
    icon?: React.ReactNode;
};

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
