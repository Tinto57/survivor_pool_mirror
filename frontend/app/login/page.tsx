"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import styles from "../components/AuthForm/AuthForm.module.css";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { isValidEmail } from "../lib/validation";

export default function LoginPage() {
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

        if (!isValidEmail(email)) {
            setError("Adresse email invalide.");
            return;
        }

        setLoading(true);
        try {
            // TODO: brancher sur POST /api/accounts/token
            // payload: { username: email, password } — l'email sert d'identifiant.
            // puis stocker le token (access/refresh) et rediriger selon le rôle.
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.card}>
                <h1 className={styles.title}>Content de vous revoir</h1>
                <p className={styles.subtitle}>Connectez-vous à votre compte CartePro</p>

                <form onSubmit={handleSubmit}>
                    <div className={styles.field}>
                        <label className={styles.label} htmlFor="email">
                            Email
                        </label>
                        <div className={styles.inputWrapper}>
                            <Mail />
                            <input
                                id="email"
                                type="email"
                                className={styles.input}
                                placeholder="ministre@ministère.gouv.fr"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                autoComplete="email"
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
        </div>
    );
}
