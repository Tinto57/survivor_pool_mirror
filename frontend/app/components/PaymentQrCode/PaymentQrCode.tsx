"use client";

import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { createPaymentIntent } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import SimulationBadge from "../SimulationBadge/SimulationBadge";
import styles from "./PaymentQrCode.module.css";

function formatCountdown(totalSeconds: number): string {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/**
 * Code de paiement réel : encode le token d'une intention de paiement
 * (POST /api/v1/payments/), à scanner par un partenaire. Le token expire après
 * 5 minutes côté API — `generation` est incrémenté à l'échéance pour redéclencher
 * l'effet de récupération et en obtenir un nouveau tant que l'écran est affiché.
 */
export default function PaymentQrCode() {
    const [token, setToken] = useState<string | null>(null);
    const [expiresAt, setExpiresAt] = useState<number | null>(null);
    const [remaining, setRemaining] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [generation, setGeneration] = useState(0);

    useEffect(() => {
        let cancelled = false;

        createPaymentIntent(getAccessToken() ?? "")
            .then((intent) => {
                if (cancelled) return;
                setToken(intent.token);
                setError(null);
                setExpiresAt(Date.now() + intent.expires_in * 1000);
            })
            .catch((err) => {
                if (cancelled) return;
                setError(err instanceof Error ? err.message : "Impossible de générer le code de paiement.");
            });

        return () => {
            cancelled = true;
        };
    }, [generation]);

    useEffect(() => {
        if (!expiresAt) return;

        const tick = () => {
            const secondsLeft = Math.max(0, Math.round((expiresAt - Date.now()) / 1000));
            setRemaining(secondsLeft);
            if (secondsLeft === 0) setGeneration((g) => g + 1);
        };

        tick();
        const interval = setInterval(tick, 1000);
        return () => clearInterval(interval);
    }, [expiresAt]);

    return (
        <div className={styles.wrap}>
            <div className={styles.header}>
                <p className={styles.title}>Votre code de paiement</p>
                <SimulationBadge size="sm" />
            </div>

            <div className={styles.frame}>
                {token ? (
                    <QRCodeSVG value={token} size={162} level="M" marginSize={0} title="Code de paiement" />
                ) : (
                    <div className={styles.placeholder} aria-hidden="true" />
                )}
            </div>

            {error ? (
                <p className={styles.error}>{error}</p>
            ) : token ? (
                <p className={styles.hint}>À présenter au partenaire · expire dans {formatCountdown(remaining)}</p>
            ) : (
                <p className={styles.hint}>Génération du code...</p>
            )}
        </div>
    );
}
