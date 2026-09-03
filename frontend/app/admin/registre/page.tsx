"use client";

import { AlertTriangle, Database, ShieldCheck } from "lucide-react";
import Page from "../../components/Page/Page";
import AdminNav from "../../components/AdminNav/AdminNav";
import { useAdminGuard } from "../useAdminGuard";
import styles from "./registre.module.css";

/**
 * Fiche de registre au sens de l'article 30 du RGPD.
 *
 * Les colonnes citées sont celles de la base qui tourne (schéma relevé le
 * 3 septembre 2026) : toute évolution du modèle doit être répercutée ici.
 */
type Record = {
    id: string;
    purpose: string;
    legalBasis: string;
    subjects: string;
    /** Tables et colonnes réelles, groupées par table. */
    data: { table: string; columns: string[]; note?: string }[];
    recipients: string[];
    retention: string;
};

const RECORDS: Record[] = [
    {
        id: "T1",
        purpose: "Gestion des comptes et authentification",
        legalBasis:
            "Exécution d'une mission d'intérêt public (art. 6.1.e) — dispositif porté par le Ministère.",
        subjects: "Salariés bénéficiaires, représentants des partenaires, agents du Ministère.",
        data: [
            {
                table: "accounts_user",
                columns: [
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "password",
                    "role",
                    "last_login",
                    "date_joined",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ],
                note: "Le mot de passe est stocké haché (PBKDF2), jamais en clair.",
            },
        ],
        recipients: [
            "Agents habilités du Ministère (accounts_user.is_staff = true)",
            "Hébergeur de la base et du serveur applicatif",
        ],
        retention:
            "13 mois à compter de la dernière connexion (accounts_user.last_login), ou de la création du compte s'il n'a jamais servi.",
    },
    {
        id: "T2",
        purpose: "Attribution et suivi du budget salarié",
        legalBasis: "Exécution d'une mission d'intérêt public (art. 6.1.e).",
        subjects: "Salariés bénéficiaires du dispositif.",
        data: [
            {
                table: "wallet_employee",
                columns: ["user_id", "employer", "balance"],
            },
            {
                table: "wallet_topup",
                columns: ["user_id", "amount", "created_at", "created_by_id"],
                note: "created_by_id identifie l'agent ou l'employeur à l'origine de l'abondement.",
            },
        ],
        recipients: [
            "Le salarié concerné",
            "L'employeur, pour les seuls abondements qu'il finance",
            "Agents habilités du Ministère",
        ],
        retention:
            "13 mois après la fin des droits du salarié ; les abondements sont conservés sur le même horizon pour justifier les montants versés.",
    },
    {
        id: "T3",
        purpose: "Référencement des partenaires et traçabilité des décisions",
        legalBasis:
            "Exécution d'une mission d'intérêt public (art. 6.1.e) et obligation de motivation des décisions administratives.",
        subjects:
            "Représentants légaux des entreprises candidates (les données d'entreprise ne relèvent du RGPD que lorsqu'elles permettent d'identifier une personne — cas de l'entrepreneur individuel).",
        data: [
            {
                table: "partners_partner",
                columns: [
                    "business_name",
                    "siren",
                    "business_purpose",
                    "address",
                    "latitude",
                    "longitude",
                    "status",
                    "registered_at",
                    "category_id",
                    "is_featured",
                ],
            },
            {
                table: "partners_partnerdecision",
                columns: ["decision", "reason", "agent_id", "created_at", "partner_id"],
                note: "Trace exigée : horodatage, identifiant de l'agent et motif écrit du refus.",
            },
        ],
        recipients: [
            "Le partenaire concerné (y compris le motif de refus qui lui est communiqué)",
            "Agents habilités du Ministère",
            "Salariés, pour les seules données publiques du catalogue (raison sociale, catégorie, adresse)",
        ],
        retention:
            "Durée du référencement, puis 13 mois. Les décisions de refus sont conservées 13 mois afin de pouvoir justifier la décision en cas de recours.",
    },
    {
        id: "T4",
        purpose: "Exécution et contrôle des paiements",
        legalBasis: "Exécution d'une mission d'intérêt public (art. 6.1.e).",
        subjects: "Salariés bénéficiaires et partenaires encaisseurs.",
        data: [
            {
                table: "transactions_qrcode",
                columns: [
                    "token",
                    "amount",
                    "created_at",
                    "expires_at",
                    "is_used",
                    "employee_id",
                ],
            },
            {
                table: "transactions_transaction",
                columns: [
                    "amount",
                    "validated_at",
                    "employee_id",
                    "partner_id",
                    "qr_code_id",
                    "is_cancelled",
                    "cancelled_at",
                    "cancelled_by_id",
                    "cancellation_reason",
                ],
                note: "Une transaction validée n'est pas supprimée : l'annulation est tracée par cancelled_at, cancelled_by_id et cancellation_reason.",
            },
        ],
        recipients: [
            "Le salarié et le partenaire parties à la transaction",
            "Agents habilités du Ministère",
        ],
        retention:
            "13 mois après la validation (transactions_transaction.validated_at). Les QR codes non consommés sont purgeables dès leur expiration (expires_at).",
    },
];

/** Données collectées dont la nécessité reste à trancher avec le conseil juridique. */
const MINIMISATION = [
    {
        column: "accounts_user.first_name / last_name",
        verdict: "à conserver",
        why: "Nécessaires pour que le partenaire identifie le porteur du droit au moment de l'encaissement.",
    },
    {
        column: "accounts_user.email",
        verdict: "à conserver",
        why: "Seul canal de récupération de compte et de notification. Aucune adresse n'est utilisée à des fins de communication.",
    },
    {
        column: "wallet_employee.employer",
        verdict: "à trancher",
        why: "Révèle l'employeur du salarié, donnée sensible en cas de fuite. Un identifiant d'employeur (clé étrangère) suffirait au fonctionnement au lieu d'un nom en clair.",
    },
    {
        column: "partners_partner.latitude / longitude",
        verdict: "à trancher",
        why: "Aucune fonction de carte n'existe aujourd'hui dans l'application : ces colonnes sont alimentées sans être utilisées.",
    },
    {
        column: "accounts_user.is_superuser",
        verdict: "à restreindre",
        why: "Aucun compte de démonstration ne doit porter ce droit ; il n'est nécessaire qu'aux comptes d'exploitation.",
    },
];

export default function RegistrePage() {
    const { admin, error } = useAdminGuard();

    if (error && !admin) return <p className={styles.error}>{error}</p>;

    if (!admin) {
        return (
            <Page title="Registre RGPD" wide>
                <div className={styles.skeleton} aria-hidden="true" />
            </Page>
        );
    }

    return (
        <Page
            title="Registre RGPD"
            subtitle="Registre des activités de traitement — article 30 du RGPD."
            wide
        >
            <div className={styles.layout}>
                <AdminNav section="registre" />

                <div className={styles.panel}>
                    <section className={styles.intro}>
                        <ShieldCheck className={styles.introIcon} aria-hidden="true" />
                        <div>
                            <p className={styles.introTitle}>
                                Responsable de traitement : Ministère du Job et Bonheur
                            </p>
                            <p className={styles.introText}>
                                Les colonnes citées ci-dessous sont celles de la base en
                                fonctionnement, relevées le 3 septembre 2026. Toute évolution du
                                modèle de données doit être répercutée dans cette fiche.
                            </p>
                        </div>
                    </section>

                    {RECORDS.map((record) => (
                        <article key={record.id} className={styles.record}>
                            <header className={styles.recordHead}>
                                <span className={styles.recordId}>{record.id}</span>
                                <h2 className={styles.recordTitle}>{record.purpose}</h2>
                            </header>

                            <dl className={styles.fields}>
                                <div className={styles.field}>
                                    <dt>Base légale</dt>
                                    <dd>{record.legalBasis}</dd>
                                </div>

                                <div className={styles.field}>
                                    <dt>Personnes concernées</dt>
                                    <dd>{record.subjects}</dd>
                                </div>

                                <div className={styles.field}>
                                    <dt>Données traitées</dt>
                                    <dd>
                                        {record.data.map((source) => (
                                            <div key={source.table} className={styles.source}>
                                                <p className={styles.table}>
                                                    <Database aria-hidden="true" />
                                                    {source.table}
                                                </p>
                                                <p className={styles.columns}>
                                                    {source.columns.map((column) => (
                                                        <code key={column} className={styles.column}>
                                                            {column}
                                                        </code>
                                                    ))}
                                                </p>
                                                {source.note && (
                                                    <p className={styles.note}>{source.note}</p>
                                                )}
                                            </div>
                                        ))}
                                    </dd>
                                </div>

                                <div className={styles.field}>
                                    <dt>Destinataires</dt>
                                    <dd>
                                        <ul className={styles.bullets}>
                                            {record.recipients.map((recipient) => (
                                                <li key={recipient}>{recipient}</li>
                                            ))}
                                        </ul>
                                    </dd>
                                </div>

                                <div className={styles.field}>
                                    <dt>Durée de conservation</dt>
                                    <dd>{record.retention}</dd>
                                </div>
                            </dl>
                        </article>
                    ))}

                    <article className={styles.record}>
                        <header className={styles.recordHead}>
                            <span className={styles.recordId}>M</span>
                            <h2 className={styles.recordTitle}>
                                Minimisation : données à arbitrer
                            </h2>
                        </header>

                        <ul className={styles.minimisation}>
                            {MINIMISATION.map((item) => (
                                <li key={item.column} className={styles.minItem}>
                                    <div className={styles.minHead}>
                                        <code className={styles.column}>{item.column}</code>
                                        <span
                                            className={
                                                item.verdict === "à conserver"
                                                    ? `${styles.verdict} ${styles.verdictKeep}`
                                                    : `${styles.verdict} ${styles.verdictReview}`
                                            }
                                        >
                                            {item.verdict}
                                        </span>
                                    </div>
                                    <p className={styles.note}>{item.why}</p>
                                </li>
                            ))}
                        </ul>
                    </article>

                    <article className={styles.record}>
                        <header className={styles.recordHead}>
                            <span className={styles.recordId}>13</span>
                            <h2 className={styles.recordTitle}>
                                Mécanisme concret des 13 mois
                            </h2>
                        </header>

                        <ol className={styles.steps}>
                            <li>
                                <strong>Purge immédiate</strong> — les QR codes expirés et non
                                consommés (<code className={styles.column}>transactions_qrcode</code>{" "}
                                où <code className={styles.column}>expires_at</code> est dépassé et{" "}
                                <code className={styles.column}>is_used</code> vaut faux) sont
                                supprimés sans délai : ils ne portent aucune valeur probante.
                            </li>
                            <li>
                                <strong>Anonymisation à 13 mois</strong> — plutôt que de supprimer
                                les transactions, qui doivent rester comptablement cohérentes, le
                                lien vers la personne est rompu : les champs identifiants de{" "}
                                <code className={styles.column}>accounts_user</code> (nom, prénom,
                                e-mail, identifiant) sont remplacés par des valeurs neutres, et le
                                compte est désactivé. Les montants et les dates subsistent, sans
                                personne derrière.
                            </li>
                            <li>
                                <strong>Suppression des comptes jamais utilisés</strong> — un compte
                                sans connexion 13 mois après sa création est supprimé, y compris ses
                                lignes <code className={styles.column}>wallet_employee</code>.
                            </li>
                            <li>
                                <strong>Décisions de référencement</strong> —{" "}
                                <code className={styles.column}>partners_partnerdecision</code> est
                                conservé 13 mois après la décision, puis{" "}
                                <code className={styles.column}>agent_id</code> est dissocié tout en
                                gardant le motif, qui n&apos;identifie personne.
                            </li>
                            <li>
                                <strong>Exécution</strong> — commande d&apos;administration dédiée (
                                <code className={styles.column}>purge_expired_data</code>),
                                idempotente, avec un mode{" "}
                                <code className={styles.column}>--dry-run</code> et un journal des
                                volumes traités à chaque passage. Reste à la brancher sur une tâche
                                planifiée quotidienne.
                            </li>
                        </ol>
                    </article>
                </div>
            </div>
        </Page>
    );
}
