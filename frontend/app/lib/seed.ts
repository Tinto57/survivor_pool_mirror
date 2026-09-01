import type { Balance, Partner, Transaction } from "./catalog";

export const SEED_PARTNERS: Partner[] = [
    {
        id: 1,
        business_name: "Poney Dream 78",
        business_purpose:
            "Club de poney familial en région parisienne. Balades en forêt, baptêmes " +
            "poney et séances de team building au grand air.",
        category: "Loisirs",
        address: "Chemin des Écuries, 78120 Rambouillet",
        city: "Rambouillet",
        latitude: 48.6436,
        longitude: 1.8297,
        status: "active",
        is_featured: true,
    },
    {
        id: 2,
        business_name: "KostumParty",
        business_purpose:
            "Magasin de déguisements et d'accessoires de fête. Location et vente, " +
            "du costume de licorne à la panoplie de ministre.",
        category: "Mode",
        address: "34 rue Oberkampf, 75011 Paris",
        city: "Paris 11e",
        latitude: 48.8649,
        longitude: 2.3721,
        status: "active",
        is_featured: true,
    },
    {
        id: 3,
        business_name: "Glaces Artisanales Corrèze",
        business_purpose:
            "Glacier artisanal corrézien. Commande en ligne et retrait en click & collect, " +
            "parfums de saison au lait de ferme.",
        category: "Alimentation",
        address: "12 place de la Guierle, 19100 Brive-la-Gaillarde",
        city: "Brive-la-Gaillarde",
        latitude: 45.1591,
        longitude: 1.5332,
        status: "active",
        is_featured: false,
    },
    {
        id: 4,
        business_name: "Chapelier Fontaine",
        business_purpose:
            "Chapeaux en feutre façonnés à la main depuis 1936. Sur-mesure, " +
            "retouches et conseil en style à l'atelier toulousain.",
        category: "Mode",
        address: "8 rue des Filatiers, 31000 Toulouse",
        city: "Toulouse",
        latitude: 43.5976,
        longitude: 1.4438,
        status: "active",
        is_featured: false,
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
