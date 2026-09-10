"use client";

import Link from "next/link";
import { Receipt } from "lucide-react";
import { useEffect, useState } from "react";
import Page from "../components/Page/Page";
import PartnerProfile from "../components/PartnerProfile/PartnerProfile";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import { getAccessToken } from "../lib/auth";
import { getPartnerMe, formatAmount } from "../lib/catalog";
import type { Partner } from "../lib/catalog";
import { ApiError, confirmPayment } from "../lib/api";
import type { ConfirmedPayment } from "../lib/api";
import styles from "./partner.module.css";
import QrScanner from "../components/QrScanner/QrScanner";

export default function PartnerHome() {
    const [partner, setPartner] = useState<Partner | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const [scannedToken, setScannedToken] = useState<string | null>(null);
    const [amountInput, setAmountInput] = useState("");
    const [confirming, setConfirming] = useState(false);
    const [confirmError, setConfirmError] = useState<string | null>(null);
    const [confirmed, setConfirmed] = useState<ConfirmedPayment | null>(null);

    useEffect(() => {
        getPartnerMe(getAccessToken())
            .then(setPartner)
            .catch((err) => setError(err instanceof Error ? err.message : "Une erreur est survenue."))
            .finally(() => setLoading(false));
    }, []);

    function handleScan(decodedText: string) {
        setScannedToken(decodedText);
        setConfirmError(null);
        setConfirmed(null);
        setAmountInput("");
    }

    function handleReset() {
        setScannedToken(null);
        setConfirmError(null);
        setConfirmed(null);
        setAmountInput("");
    }

    async function handleConfirm() {
        const amount = Number(amountInput.replace(",", "."));
        const token = getAccessToken();

        if (!scannedToken || !token || !Number.isFinite(amount) || amount <= 0) {
            setConfirmError("Saisissez un montant supérieur à 0.");
            return;
        }

        setConfirming(true);
        setConfirmError(null);

        try {
            const transaction = await confirmPayment(scannedToken, amount, token);
            setConfirmed(transaction);
        } catch (err) {
            setConfirmError(err instanceof ApiError ? err.message : "Le paiement a échoué.");
        } finally {
            setConfirming(false);
        }
    }

    if (loading) {
        return (
            <Page title="Partenaire">
                <p className={styles.info}>Chargement...</p>
            </Page>
        );
    }

    if (error || !partner) {
        return (
            <Page title="Erreur">
                <p className={styles.info}>
                    {error ?? "Une erreur est survenue lors du chargement de votre profil"}
                </p>
            </Page>
        );
    }

    return (
        <main className={styles.page}>
            <PartnerProfile partner={partner} />

            <Link href="/transactions-partenaire" className={styles.historyLink}>
                <Receipt aria-hidden="true" size={18} />
                Voir l&apos;historique des transactions
            </Link>

            <section className={styles.scanCard}>
                <div className={styles.scanHeader}>
                    <p className={styles.scanTitle}>Encaisser un paiement</p>
                    <SimulationBadge size="sm" />
                </div>

                {confirmed ? (
                    <div className={styles.result}>
                        <p className={styles.resultAmount}>{formatAmount(Number(confirmed.amount))}</p>
                        <p className={styles.resultHint}>Paiement validé.</p>
                        <button type="button" className={styles.secondaryButton} onClick={handleReset}>
                            Scanner un nouveau code
                        </button>
                    </div>
                ) : scannedToken ? (
                    <div className={styles.confirmForm}>
                        <label className={styles.label} htmlFor="payment-amount">
                            Montant à encaisser
                        </label>
                        <input
                            id="payment-amount"
                            className={styles.amountInput}
                            type="text"
                            inputMode="decimal"
                            placeholder="0,00"
                            value={amountInput}
                            onChange={(e) => setAmountInput(e.target.value)}
                            autoFocus
                        />

                        {confirmError && <p className={styles.confirmError}>{confirmError}</p>}

                        <div className={styles.confirmActions}>
                            <button
                                type="button"
                                className={styles.secondaryButton}
                                onClick={handleReset}
                                disabled={confirming}
                            >
                                Annuler
                            </button>
                            <button
                                type="button"
                                className={styles.primaryButton}
                                onClick={handleConfirm}
                                disabled={confirming}
                            >
                                {confirming ? "Validation..." : "Valider le paiement"}
                            </button>
                        </div>
                    </div>
                ) : (
                    <QrScanner onScan={handleScan} />
                )}
            </section>
        </main>
    );
}
