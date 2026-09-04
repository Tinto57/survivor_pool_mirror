"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
    BadgeCheck,
    Ban,
    Check,
    Heart,
    Inbox,
    Landmark,
    LogOut,
    Store,
    Users,
} from "lucide-react";
import Page from "../components/Page/Page";
import AdminNav from "../components/AdminNav/AdminNav";
import type { DashboardTab } from "../components/AdminNav/AdminNav";
import SimulationBadge from "../components/SimulationBadge/SimulationBadge";
import Avatar from "../components/Avatar/Avatar";
import { ApiError, creditEmployee } from "../lib/api";
import { getAccessToken, logout } from "../lib/auth";
import { useAdminGuard } from "./useAdminGuard";
import {
    formatAmount,
    formatDate,
    formatDateTime,
    getEmployees,
    getPartnerDecisions,
    getPartners,
    getTransactions,
} from "../lib/catalog";
import type { AdminEmployee, Partner, PartnerDecision, Transaction } from "../lib/catalog";
import styles from "./admin.module.css";

const STATUS_LABEL: Record<Partner["status"], string> = {
    pending: "En attente",
    active: "Référencé",
    suspended: "Suspendu",
    closed: "Refusé",
};

export default function AdminHome() {
    const router = useRouter();
    const { admin, error: guardError } = useAdminGuard();

    const [partners, setPartners] = useState<Partner[]>([]);
    const [employees, setEmployees] = useState<AdminEmployee[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [decisions, setDecisions] = useState<PartnerDecision[]>([]);

    const [tab, setTab] = useState<DashboardTab>("requests");
    const [rejecting, setRejecting] = useState<number | null>(null);
    const [reason, setReason] = useState("");
    const [crediting, setCrediting] = useState<number | null>(null);
    const [creditAmount, setCreditAmount] = useState("");
    const [notice, setNotice] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Les données ne sont chargées qu'une fois la session d'admin confirmée.
    useEffect(() => {
        if (!admin) return;

        const token = getAccessToken();

        Promise.all([getPartners(token), getEmployees(token), getTransactions(token)])
            .then(([nextPartners, nextEmployees, nextTransactions]) => {
                setPartners(nextPartners);
                setEmployees(nextEmployees);
                setTransactions(nextTransactions);
                setDecisions(getPartnerDecisions());
            })
            .catch((err) => {
                setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
            });
    }, [admin]);

    const pending = useMemo(() => partners.filter((p) => p.status === "pending"), [partners]);
    const referenced = useMemo(
        () => partners.filter((p) => p.status === "active"),
        [partners],
    );

    const totals = useMemo(() => {
        // Une transaction annulée/contre-passée a counter_entry_of non-nul
        const active = transactions.filter((t) => t.counter_entry_of === null);

        const payments = active.filter((t) => t.transaction_type === "PAYMENT");

        return {
            distributed:
                employees.reduce((sum, e) => sum + Number(e.balance), 0) +
                payments.reduce((s, t) => s + Number(t.amount), 0),
            spent: payments.reduce((sum, t) => sum + Number(t.amount), 0),
        };
    }, [employees, transactions]);

    /** Enregistre la décision dans le journal : horodatage, agent, motif écrit. */
    function recordDecision(partner: Partner, decision: PartnerDecision["decision"], why: string) {
        setDecisions((current) => [
            {
                id: Math.max(0, ...current.map((d) => d.id)) + 1,
                partner_id: partner.id,
                partner_name: partner.business_name,
                decision,
                reason: why,
                agent: admin?.username ?? "inconnu",
                created_at: new Date().toISOString(),
            },
            ...current,
        ]);
    }

    function handleAccept(partner: Partner) {
        setPartners((current) =>
            current.map((p) => (p.id === partner.id ? { ...p, status: "active" } : p)),
        );
        recordDecision(partner, "accepted", "Dossier conforme, SIREN et objet social vérifiés.");
        setNotice(`${partner.business_name} est désormais référencé.`);
    }

    function handleReject(partner: Partner) {
        if (!reason.trim()) return;

        setPartners((current) =>
            current.map((p) => (p.id === partner.id ? { ...p, status: "closed" } : p)),
        );
        recordDecision(partner, "rejected", reason.trim());
        setNotice(`Refus enregistré pour ${partner.business_name}, avec son motif.`);
        setRejecting(null);
        setReason("");
    }

    function handleToggleFeatured(partner: Partner) {
        setPartners((current) =>
            current.map((p) =>
                p.id === partner.id ? { ...p, is_featured: !p.is_featured } : p,
            ),
        );
        setNotice(
            partner.is_featured
                ? `${partner.business_name} retiré du Coup de cœur du Ministre.`
                : `${partner.business_name} mis en avant sur l'accueil salarié.`,
        );
    }

    async function handleCredit(employee: AdminEmployee) {
        const amount = Number(creditAmount.replace(",", "."));
        const token = getAccessToken();

        if (!token || !Number.isFinite(amount) || amount <= 0) {
            setError("Saisissez un montant supérieur à 0.");
            return;
        }

        setError(null);

        try {
            const updated = await creditEmployee(employee.id, amount, token);

            setEmployees((current) =>
                current.map((e) =>
                    e.id === employee.id ? { ...e, balance: updated.balance } : e,
                ),
            );
            setNotice(`Abondement de ${formatAmount(amount)} crédité au salarié n°${employee.id}.`);
            setCrediting(null);
            setCreditAmount("");
        } catch (err) {
            setError(err instanceof ApiError ? err.message : "L'abondement a échoué.");
        }
    }

    function handleLogout() {
        logout();
        router.replace("/login");
    }

    if (guardError && !admin) return <p className={styles.error}>{guardError}</p>;

    if (!admin) {
        return (
            <Page title="Espace Ministère">
                <div className={styles.skeleton} aria-hidden="true" />
            </Page>
        );
    }

    return (
        <Page
            title="Espace Ministère"
            subtitle={`Connecté en tant que ${admin.username}.`}
            simulation
            wide
            aside={
                <button type="button" className={styles.logout} onClick={handleLogout}>
                    <LogOut aria-hidden="true" />
                    Déconnexion
                </button>
            }
        >
            <section className={styles.stats} aria-label="Tableau de bord national">
                <div className={styles.stat}>
                    <Users className={styles.statIcon} aria-hidden="true" />
                    <p className={styles.statValue}>{employees.length}</p>
                    <p className={styles.statLabel}>Salariés</p>
                </div>

                <div className={styles.stat}>
                    <Store className={styles.statIcon} aria-hidden="true" />
                    <p className={styles.statValue}>{referenced.length}</p>
                    <p className={styles.statLabel}>Partenaires référencés</p>
                </div>

                <div className={styles.stat}>
                    <Inbox className={styles.statIcon} aria-hidden="true" />
                    <p className={styles.statValue}>{pending.length}</p>
                    <p className={styles.statLabel}>Demandes en attente</p>
                </div>

                <div className={styles.stat}>
                    <Landmark className={styles.statIcon} aria-hidden="true" />
                    <p className={styles.statValue}>{formatAmount(totals.distributed)}</p>
                    <p className={styles.statLabel}>
                        Budget distribué <SimulationBadge size="sm" />
                    </p>
                </div>

                <div className={styles.stat}>
                    <BadgeCheck className={styles.statIcon} aria-hidden="true" />
                    <p className={styles.statValue}>{formatAmount(totals.spent)}</p>
                    <p className={styles.statLabel}>
                        Dépensé chez les partenaires <SimulationBadge size="sm" />
                    </p>
                </div>
            </section>

            {notice && (
                <p className={styles.notice} role="status">
                    {notice}
                </p>
            )}
            {error && <p className={styles.error}>{error}</p>}

            <div className={styles.layout}>
                <AdminNav
                    section="dashboard"
                    activeTab={tab}
                    onSelectTab={setTab}
                    pendingCount={pending.length}
                />

                <div className={styles.panel}>
            {tab === "requests" &&
                (pending.length === 0 ? (
                    <p className={styles.empty}>Aucune demande d&apos;inscription en attente.</p>
                ) : (
                    <ul className={styles.list}>
                        {pending.map((partner) => (
                            <li key={partner.id} className={styles.request}>
                                <div className={styles.requestHead}>
                                    <Avatar name={partner.business_name} />
                                    <div>
                                        <p className={styles.requestName}>{partner.business_name}</p>
                                        <p className={styles.requestMeta}>
                                            {partner.category} · {partner.city} · demande du{" "}
                                            {formatDate(partner.registered_at)}
                                        </p>
                                    </div>
                                </div>

                                <dl className={styles.facts}>
                                    <div className={styles.fact}>
                                        <dt>SIREN</dt>
                                        <dd>{partner.siren}</dd>
                                    </div>
                                    <div className={styles.fact}>
                                        <dt>Adresse</dt>
                                        <dd>{partner.address}</dd>
                                    </div>
                                    <div className={styles.fact}>
                                        <dt>Objet social</dt>
                                        <dd>{partner.business_purpose}</dd>
                                    </div>
                                </dl>

                                {rejecting === partner.id ? (
                                    <div className={styles.rejectBox}>
                                        <label className={styles.rejectLabel} htmlFor={`motif-${partner.id}`}>
                                            Motif du refus (obligatoire, communiqué au partenaire)
                                        </label>
                                        <textarea
                                            id={`motif-${partner.id}`}
                                            className={styles.textarea}
                                            rows={3}
                                            value={reason}
                                            onChange={(e) => setReason(e.target.value)}
                                            placeholder="Ex. : activité hors du périmètre du dispositif."
                                        />
                                        <div className={styles.actions}>
                                            <button
                                                type="button"
                                                className={styles.reject}
                                                disabled={!reason.trim()}
                                                onClick={() => handleReject(partner)}
                                            >
                                                Confirmer le refus
                                            </button>
                                            <button
                                                type="button"
                                                className={styles.ghost}
                                                onClick={() => {
                                                    setRejecting(null);
                                                    setReason("");
                                                }}
                                            >
                                                Annuler
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className={styles.actions}>
                                        <button
                                            type="button"
                                            className={styles.accept}
                                            onClick={() => handleAccept(partner)}
                                        >
                                            <Check aria-hidden="true" />
                                            Référencer
                                        </button>
                                        <button
                                            type="button"
                                            className={styles.ghost}
                                            onClick={() => {
                                                setRejecting(partner.id);
                                                setReason("");
                                            }}
                                        >
                                            <Ban aria-hidden="true" />
                                            Refuser
                                        </button>
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>
                ))}

            {tab === "partners" &&
                (referenced.length === 0 ? (
                    <p className={styles.empty}>Aucun partenaire référencé pour le moment.</p>
                ) : (
                    <ul className={styles.list}>
                        {referenced.map((partner) => (
                            <li key={partner.id} className={styles.row}>
                                <Avatar name={partner.business_name} size="sm" />

                                <div className={styles.rowBody}>
                                    <p className={styles.rowName}>{partner.business_name}</p>
                                    <p className={styles.rowMeta}>
                                        {partner.category} · {partner.city}
                                    </p>
                                </div>

                                <span className={styles.siren}>SIREN {partner.siren}</span>

                                <span className={styles.pill}>{STATUS_LABEL[partner.status]}</span>

                                <button
                                    type="button"
                                    className={
                                        partner.is_featured
                                            ? `${styles.feature} ${styles.featureOn}`
                                            : styles.feature
                                    }
                                    aria-pressed={partner.is_featured}
                                    title="Coup de cœur du Ministre"
                                    onClick={() => handleToggleFeatured(partner)}
                                >
                                    <Heart aria-hidden="true" />
                                    <span className={styles.featureLabel}>Coup de cœur</span>
                                </button>
                            </li>
                        ))}
                    </ul>
                ))}

            {tab === "employees" && (
                <ul className={styles.list}>
                    {employees.map((employee) => (
                        <li key={employee.id} className={styles.row}>
                            <Avatar name={`Salarié ${employee.id}`} size="sm" />

                            <div className={styles.rowBody}>
                                <p className={styles.rowName}>Salarié n°{employee.id}</p>
                                <p className={styles.rowMeta}>Compte actif</p>
                            </div>

                            <span className={styles.siren}>{employee.employer}</span>

                            <span className={styles.balance}>
                                {formatAmount(Number(employee.balance))}
                                <SimulationBadge size="sm" />
                            </span>

                            {crediting === employee.id ? (
                                <div className={styles.creditBox}>
                                    <input
                                        type="text"
                                        inputMode="decimal"
                                        className={styles.creditInput}
                                        value={creditAmount}
                                        onChange={(e) => setCreditAmount(e.target.value)}
                                        placeholder="50,00"
                                        aria-label="Montant de l'abondement en euros"
                                    />
                                    <button
                                        type="button"
                                        className={styles.accept}
                                        onClick={() => handleCredit(employee)}
                                    >
                                        Créditer
                                    </button>
                                    <button
                                        type="button"
                                        className={styles.ghost}
                                        onClick={() => {
                                            setCrediting(null);
                                            setCreditAmount("");
                                        }}
                                    >
                                        Annuler
                                    </button>
                                </div>
                            ) : (
                                <button
                                    type="button"
                                    className={styles.ghost}
                                    onClick={() => {
                                        setCrediting(employee.id);
                                        setCreditAmount("");
                                        setError(null);
                                    }}
                                >
                                    Abonder
                                </button>
                            )}
                        </li>
                    ))}
                </ul>
            )}

            {tab === "journal" && (
                <ul className={styles.list}>
                    {decisions.map((decision) => (
                        <li key={decision.id} className={styles.decision}>
                            <span
                                className={
                                    decision.decision === "accepted"
                                        ? `${styles.tag} ${styles.tagAccepted}`
                                        : `${styles.tag} ${styles.tagRejected}`
                                }
                            >
                                {decision.decision === "accepted" ? "Référencé" : "Refusé"}
                            </span>

                            <div className={styles.rowBody}>
                                <p className={styles.rowName}>{decision.partner_name}</p>
                                <p className={styles.reason}>{decision.reason}</p>
                                <p className={styles.rowMeta}>
                                    {formatDateTime(decision.created_at)} · agent {decision.agent}
                                </p>
                            </div>
                        </li>
                    ))}
                </ul>
            )}
                </div>
            </div>
        </Page>
    );
}
