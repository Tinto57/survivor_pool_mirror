import type { PartnerDecision } from "./catalog";

export const SEED_DECISIONS: PartnerDecision[] = [
    {
        id: 4,
        partner_id: 5,
        partner_name: "Librairie du Vieux Port",
        decision: "accepted",
        reason: "SIREN vérifié, objet social conforme au périmètre culture.",
        agent: "admin.demo",
        created_at: "2026-08-11T10:52:00",
    },
    {
        id: 3,
        partner_id: 4,
        partner_name: "Pharmacie du Parc",
        decision: "accepted",
        reason: "Autorisation d'exercice vérifiée, officine à jour de son agrément.",
        agent: "admin.demo",
        created_at: "2026-08-03T16:41:00",
    },
    {
        id: 2,
        partner_id: 12,
        partner_name: "Cave à Whisky du Marais",
        decision: "rejected",
        reason:
            "Activité de vente d'alcool exclue du périmètre du dispositif " +
            "(article 3 des conditions de référencement).",
        agent: "admin.demo",
        created_at: "2026-07-29T09:14:00",
    },
    {
        id: 1,
        partner_id: 3,
        partner_name: "Librairie Vasseur",
        decision: "accepted",
        reason: "SIREN vérifié, objet social conforme au périmètre culture.",
        agent: "admin.demo",
        created_at: "2026-07-25T12:03:00",
    },
];
