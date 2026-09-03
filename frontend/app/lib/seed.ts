import type {
    AdminEmployee,
    Balance,
    Partner,
    PartnerDecision,
    Transaction,
} from "./catalog";

export const SEED_PARTNERS: Partner[] = [
    {
        id: 1,
        business_name: "Poney Dream 78",
        business_purpose:
            "Club de poney familial en région parisienne. Balades en forêt, baptêmes " +
            "poney et séances de team building au grand air.",
        category: "Loisirs",
        siren: "812457903",
        address: "Chemin des Écuries, 78120 Rambouillet",
        city: "Rambouillet",
        latitude: 48.6436,
        longitude: 1.8297,
        status: "active",
        is_featured: true,
        registered_at: "2026-07-12T09:20:00",
    },
    {
        id: 2,
        business_name: "KostumParty",
        business_purpose:
            "Magasin de déguisements et d'accessoires de fête. Location et vente, " +
            "du costume de licorne à la panoplie de ministre.",
        category: "Mode",
        siren: "504338712",
        address: "34 rue Oberkampf, 75011 Paris",
        city: "Paris 11e",
        latitude: 48.8649,
        longitude: 2.3721,
        status: "active",
        is_featured: true,
        registered_at: "2026-07-18T14:05:00",
    },
    {
        id: 3,
        business_name: "Glaces Artisanales Corrèze",
        business_purpose:
            "Glacier artisanal corrézien. Commande en ligne et retrait en click & collect, " +
            "parfums de saison au lait de ferme.",
        category: "Alimentation",
        siren: "789112045",
        address: "12 place de la Guierle, 19100 Brive-la-Gaillarde",
        city: "Brive-la-Gaillarde",
        latitude: 45.1591,
        longitude: 1.5332,
        status: "active",
        is_featured: false,
        registered_at: "2026-07-25T11:40:00",
    },
    {
        id: 4,
        business_name: "Chapelier Fontaine",
        business_purpose:
            "Chapeaux en feutre façonnés à la main depuis 1936. Sur-mesure, " +
            "retouches et conseil en style à l'atelier toulousain.",
        category: "Mode",
        siren: "331904568",
        address: "8 rue des Filatiers, 31000 Toulouse",
        city: "Toulouse",
        latitude: 43.5976,
        longitude: 1.4438,
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
];

export const SEED_EMPLOYEES: AdminEmployee[] = [
    { id: 1, user: 1, balance: "132.50", employer: "Ministère du Job et Bonheur" },
    { id: 2, user: 4, balance: "78.00", employer: "Ministère du Job et Bonheur" },
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
        partner_name: "Chapelier Fontaine",
        decision: "accepted",
        reason: "Artisan d'art référencé, dossier complet.",
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
        partner_name: "Glaces Artisanales Corrèze",
        decision: "accepted",
        reason: "Producteur local, SIREN actif au répertoire.",
        agent: "admin.demo",
        created_at: "2026-07-25T12:03:00",
    },
];

export const SEED_BALANCE: Balance = {
    amount: 132.5,
    employer: "Ministère du Job et Bonheur",
    topped_up_this_month: 180,
    spent_this_month: 47.5,
};

export const SEED_TRANSACTIONS: Transaction[] = [
    {
        id: 8,
        amount: 180,
        kind: "topup",
        validated_at: "2026-09-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        is_cancelled: false,
    },
    {
        id: 7,
        amount: 24,
        kind: "payment",
        validated_at: "2026-08-29T16:12:00",
        partner_id: 1,
        partner_name: "Poney Dream 78",
        is_cancelled: false,
    },
    {
        id: 6,
        amount: 8.5,
        kind: "payment",
        validated_at: "2026-08-27T14:35:00",
        partner_id: 3,
        partner_name: "Glaces Artisanales Corrèze",
        is_cancelled: false,
    },
    {
        id: 5,
        amount: 15,
        kind: "payment",
        validated_at: "2026-08-22T11:05:00",
        partner_id: 2,
        partner_name: "KostumParty",
        is_cancelled: false,
    },
    {
        id: 4,
        amount: 62,
        kind: "payment",
        validated_at: "2026-08-14T18:40:00",
        partner_id: 4,
        partner_name: "Chapelier Fontaine",
        is_cancelled: true,
    },
    {
        id: 3,
        amount: 150,
        kind: "topup",
        validated_at: "2026-08-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        is_cancelled: false,
    },
    {
        id: 2,
        amount: 32,
        kind: "payment",
        validated_at: "2026-07-19T13:20:00",
        partner_id: 1,
        partner_name: "Poney Dream 78",
        is_cancelled: false,
    },
    {
        id: 1,
        amount: 150,
        kind: "topup",
        validated_at: "2026-07-01T08:00:00",
        partner_id: null,
        partner_name: "Abondement employeur",
        is_cancelled: false,
    },
];
