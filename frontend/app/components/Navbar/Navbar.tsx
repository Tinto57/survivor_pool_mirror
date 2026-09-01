import Link from "next/link";
import styles from "./Navbar.module.css";

import {
    House,
    History,
    ShoppingBag,
} from "lucide-react";

export default function Navbar() {
    return (
        <nav className={styles.navbar}>
            <Link href="/" className={styles.navbarLogo}>
                <span>CartePro</span>
            </Link>

            <div className={styles.navbarLinks}>
                <Link href="/">
                    <House />
                </Link>

                <Link href="/historique">
                    <History />
                </Link>

                <Link href="/catalogue">
                    <ShoppingBag />
                </Link>
            </div>
        </nav>
    );
}