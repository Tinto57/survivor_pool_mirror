"use client";

import { QRCodeSVG } from "qrcode.react";
import SimulationBadge from "../SimulationBadge/SimulationBadge";
import styles from "./FakeQrCode.module.css";

/**
 * Aperçu factice : le code encode un identifiant de démo statique, rien n'est généré
 * ni signé côté serveur. À remplacer par le vrai flux de paiement une fois développé.
 */
const DEMO_PAYLOAD = "TICKETTOUT-SIMULATION-DEMO";

export default function FakeQrCode() {
    return (
        <div className={styles.wrap}>
            <div className={styles.header}>
                <p className={styles.title}>Votre code de paiement</p>
                <SimulationBadge size="sm" />
            </div>

            <div className={styles.frame}>
                <QRCodeSVG
                    value={DEMO_PAYLOAD}
                    size={162}
                    level="M"
                    marginSize={0}
                    title="Code de paiement (simulation)"
                />
            </div>

            <p className={styles.hint}>À présenter au partenaire au moment du paiement.</p>
        </div>
    );
}
