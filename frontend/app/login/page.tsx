"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "../components/AuthForm/AuthForm.module.css";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { ApiError, login } from "../lib/api";
import { homePathForRole, startSession } from "../lib/auth";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);

        if (!email || !password) {
            setError("Merci de remplir tous les champs.");
            return;
        }

        setLoading(true);
        try {
            const { user, token } = await login(email, password);

            startSession(user, token);
            router.push(homePathForRole(user.role));
        } catch (err) {
            if (err instanceof ApiError && err.status === 401) {
                setError("Email ou mot de passe incorrect.");
            } else {
                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            }
            setLoading(false);
        }
    }

    return (
        <main className={styles.wrapper}>
            <div className={styles.card}>
                <h1 className={styles.title}>Content de vous revoir</h1>
                <p className={styles.subtitle}>Connectez-vous à votre compte Ticket Tout</p>

                <form onSubmit={handleSubmit}>
                    <div className={styles.field}>
                        <label className={styles.label} htmlFor="email">
                            Identifiant
                        </label>
                        <div className={styles.inputWrapper}>
                            <Mail />
                            <input
                                id="email"
                                type="text"
                                className={styles.input}
                                placeholder="salarie.demo"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                autoComplete="username"
                            />
                        </div>
                    </div>

                    <div className={styles.field}>
                        <label className={styles.label} htmlFor="password">
                            Mot de passe
                        </label>
                        <div className={styles.inputWrapper}>
                            <Lock />
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                className={styles.input}
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete="current-password"
                            />
                            <button
                                type="button"
                                className={styles.passwordToggle}
                                onClick={() => setShowPassword((v) => !v)}
                                aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                            >
                                {showPassword ? <EyeOff /> : <Eye />}
                            </button>
                        </div>
                    </div>

                    {error && <p className={styles.error}>{error}</p>}

                    <button type="submit" className={styles.submit} disabled={loading}>
                        {loading ? "Connexion..." : "Se connecter"}
                    </button>
                </form>

                <p className={styles.switch}>
                    Vous êtes un partenaire et n&apos;avez pas de compte ?{" "}
                    <Link href="/register">Créer un compte partenaire</Link>
                </p>
            </div>
        </main>
    );
}
