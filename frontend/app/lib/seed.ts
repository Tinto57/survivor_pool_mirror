import type {
    AdminEmployee,
    Balance,
    MinisterSpotlight,
    Partner,
    PartnerDecision,
    Transaction,
} from "./catalog";

export const SEED_PARTNERS: Partner[] = [
    {
        id: 1,
        business_name: "Le Comptoir du Midi",
        business_purpose:
            "Restaurant de quartier, cuisine du Sud-Ouest et menu du jour. Formule " +
            "salariés avec addition fractionnable en fin de service.",
        category: "Restauration",
        siren: "267914530",
        address: "6 rue du Taur, 31000 Toulouse",
        city: "Toulouse",
        latitude: 43.6047,
        longitude: 1.4442,
        status: "active",
        is_featured: true,
        registered_at: "2026-07-12T09:20:00",
    },
    {
        id: 2,
        business_name: "Épicerie Sainte-Claire",
        business_purpose:
            "Épicerie de proximité, produits frais et locaux. Livraison possible " +
            "sur le quartier en fin de journée.",
        category: "Alimentation",
        siren: "398215647",
        address: "14 rue Sainte-Claire, 38000 Grenoble",
        city: "Grenoble",
        latitude: 45.1885,
        longitude: 5.7245,
        status: "active",
        is_featured: true,
        registered_at: "2026-07-18T14:05:00",
    },
    {
        id: 3,
        business_name: "Librairie Vasseur",
        business_purpose:
            "Librairie indépendante généraliste, littérature et bandes dessinées. " +
            "Rencontres d'auteurs organisées un samedi par mois.",
        category: "Culture",
        siren: "145762893",
        address: "9 rue des Trois Cailloux, 80000 Amiens",
        city: "Amiens",
        latitude: 49.8942,
        longitude: 2.2957,
        status: "active",
        is_featured: false,
        registered_at: "2026-07-25T11:40:00",
    },
    {
        id: 4,
        business_name: "Pharmacie du Parc",
        business_purpose:
            "Pharmacie de quartier, conseil officinal et service de garde. " +
            "Bilan de médication proposé sur rendez-vous.",
        category: "Santé",
        siren: "683920174",
        address: "2 place du Parc, 69006 Lyon",
        city: "Lyon",
        latitude: 45.7797,
        longitude: 4.8422,
        status: "active",
        is_featured: false,
        registered_at: "2026-08-03T16:15:00",
    },
    {
        id: 5,
        business_name: "Librairie du Vieux Port",
        business_purpose:
            "Librairie indépendante généraliste. Fonds littérature, jeunesse et " +
            "sciences humaines, avec un rayon régional marseillais.",
        category: "Culture",
        siren: "452087336",
        address: "21 quai du Port, 13002 Marseille",
        city: "Marseille 2e",
        latitude: 43.2951,
        longitude: 5.3698,
        status: "active",
        is_featured: false,
        registered_at: "2026-08-11T10:30:00",
    },
    {
        id: 6,
        business_name: "Cinéma Le Rex Ambulant",
        business_purpose:
            "Cinéma itinérant desservant vingt-deux communes rurales des Vosges. " +
            "Séances en salle des fêtes et projections de plein air en été.",
        category: "Culture",
        siren: "902114780",
        address: "4 rue de la Gare, 88000 Épinal",
        city: "Épinal",
        latitude: 48.1744,
        longitude: 6.4512,
        status: "pending",
        is_featured: false,
        registered_at: "2026-09-01T08:45:00",
    },
    {
        id: 7,
        business_name: "Boulangerie Mercier & Fils",
        business_purpose:
            "Boulangerie-pâtisserie artisanale, pains au levain et viennoiserie pur " +
            "beurre. Trois points de vente en centre-ville de Lille.",
        category: "Alimentation",
        siren: "637229015",
        address: "17 rue Esquermoise, 59000 Lille",
        city: "Lille",
        latitude: 50.6389,
        longitude: 3.0623,
        status: "pending",
        is_featured: false,
        registered_at: "2026-09-02T13:12:00",
    },
    {
        id: 8,
        business_name: "Atelier Vélo Solidaire",
        business_purpose:
            "Atelier associatif de réparation de vélos et vente de cycles reconditionnés. " +
            "Ateliers d'auto-réparation ouverts le samedi.",
        category: "Loisirs",
        siren: "884503271",
        address: "9 rue Pasteur, 44000 Nantes",
        city: "Nantes",
        latitude: 47.2141,
        longitude: -1.5534,
        status: "pending",
        is_featured: false,
        registered_at: "2026-09-03T07:28:00",
    },
    {
        id: 9,
        business_name: "Thermes de Bagnères",
        business_purpose:
            "Établissement thermal et spa. Cures bien-être, hammam et soins de " +
            "récupération pour les salariés en horaires décalés.",
        category: "Bien-être",
        siren: "715660824",
        address: "1 allée des Coustous, 65200 Bagnères-de-Bigorre",
        city: "Bagnères-de-Bigorre",
        latitude: 43.0642,
        longitude: 0.1494,
        status: "pending",
        is_featured: false,
        registered_at: "2026-09-03T09:03:00",
    },
    {
        id: 10,
        business_name: "Transports Régionaux Unifiés",
        business_purpose:
            "Réseau d'autocars interurbains. Abonnement mensuel domicile-travail " +
            "avec tarif préférentiel salariés.",
        category: "Mobilité",
        siren: "926471358",
        address: "12 avenue de la Gare, 67000 Strasbourg",
        city: "Strasbourg",
        latitude: 48.5734,
        longitude: 7.7521,
        status: "active",
        is_featured: false,
        registered_at: "2026-09-04T08:15:00",
    },
    {
        id: 11,
        business_name: "Sport Loisirs Aubagne",
        business_purpose:
            "Complexe sportif associatif. Cours collectifs, salle de musculation " +
            "et créneaux libres en soirée.",
        category: "Sport",
        siren: "517038642",
        address: "5 avenue Antide Boyer, 13400 Aubagne",
        city: "Aubagne",
        latitude: 43.293,
        longitude: 5.5701,
        status: "active",
        is_featured: false,
        registered_at: "2026-09-04T10:40:00",
    },
];

export const SEED_EMPLOYEES: AdminEmployee[] = [
    { id: 1, user: 1, balance: "132.50", employer: "Ticket Tout" },
    { id: 2, user: 4, balance: "78.00", employer: "Ticket Tout" },
    { id: 3, user: 5, balance: "215.40", employer: "Mairie de Nancy" },
    { id: 4, user: 6, balance: "46.90", employer: "Mairie de Nancy" },
    { id: 5, user: 7, balance: "180.00", employer: "Agence Régionale de Santé Grand Est" },
    { id: 6, user: 8, balance: "12.30", employer: "Agence Régionale de Santé Grand Est" },
    { id: 7, user: 9, balance: "97.75", employer: "Rectorat de Nancy-Metz" },
];

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

export const SEED_BALANCE: Balance = {
    amount: 132.5,
    employer: "Ticket Tout",
    topped_up_this_month: 180,
    spent_this_month: 47.5,
};

export const SEED_TRANSACTIONS: Transaction[] = [
    {
        id: 8,
        amount: 180,
        transaction_type: "ABONDMENT",
        validated_at: "2026-09-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        counter_entry_of: null,
        balance_after: 132.5,
    },
    {
        id: 7,
        amount: 24,
        transaction_type: "PAYMENT",
        validated_at: "2026-08-29T16:12:00",
        partner_id: 1,
        partner_name: "Le Comptoir du Midi",
        counter_entry_of: null,
        balance_after: -47.5,
    },
    {
        id: 6,
        amount: 8.5,
        transaction_type: "PAYMENT",
        validated_at: "2026-08-27T14:35:00",
        partner_id: 3,
        partner_name: "Librairie Vasseur",
        counter_entry_of: null,
        balance_after: -23.5,
    },
    {
        id: 5,
        amount: 15,
        transaction_type: "PAYMENT",
        validated_at: "2026-08-22T11:05:00",
        partner_id: 2,
        partner_name: "Épicerie Sainte-Claire",
        counter_entry_of: null,
        balance_after: -15,
    },
    {
        id: 4,
        amount: 62,
        transaction_type: "PAYMENT",
        validated_at: "2026-08-14T18:40:00",
        partner_id: 4,
        partner_name: "Pharmacie du Parc",
        counter_entry_of: null,
        balance_after: 0,
    },
    {
        id: 3,
        amount: 150,
        transaction_type: "ABONDMENT",
        validated_at: "2026-08-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        counter_entry_of: null,
        balance_after: 62,
    },
    {
        id: 2,
        amount: 32,
        transaction_type: "PAYMENT",
        validated_at: "2026-07-19T13:20:00",
        partner_id: 1,
        partner_name: "Le Comptoir du Midi",
        counter_entry_of: null,
        balance_after: -88,
    },
    {
        id: 1,
        amount: 150,
        transaction_type: "ABONDMENT",
        validated_at: "2026-07-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        counter_entry_of: null,
        balance_after: -56,
    },
];

export const SEED_SPOTLIGHT: MinisterSpotlight = {
    id: 3,
    partner: {
        id: 4,
        business_name: "Pharmacie du Parc",
        category: "Santé",
        address: "2 place du Parc, 69006 Lyon",
    },
    message:
        "Un accueil comme on n'en fait plus. Foncez à la Pharmacie du Parc, vous ne le regretterez pas !",
    is_active: true,
    click_count: 214,
    published_by: "ministre.berlier",
    published_at: "2026-09-05T07:30:00",
};

export const SEED_SPOTLIGHT_HISTORY: MinisterSpotlight[] = [
    SEED_SPOTLIGHT,
    {
        id: 2,
        partner: {
            id: 1,
            business_name: "Le Comptoir du Midi",
            category: "Restauration",
            address: "6 rue du Taur, 31000 Toulouse",
        },
        message: "Un bon plat de saison, ça n'a pas de prix (enfin si, mais c'est nous qui payons).",
        is_active: false,
        click_count: 856,
        published_by: "ministre.berlier",
        published_at: "2026-08-20T09:00:00",
    },
    {
        id: 1,
        partner: {
            id: 5,
            business_name: "Librairie du Vieux Port",
            category: "Culture",
            address: "21 quai du Port, 13002 Marseille",
        },
        message: "La culture, ça se cultive. Un détour par cette librairie marseillaise s'impose.",
        is_active: false,
        click_count: 431,
        published_by: "ministre.berlier",
        published_at: "2026-08-05T09:00:00",
    },
];
