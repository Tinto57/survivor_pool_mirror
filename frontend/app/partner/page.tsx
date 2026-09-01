"use client";

import Page from "../components/Page/Page";
import SessionNotice from "../components/SessionNotice/SessionNotice";

export default function PartnerHome() {
    return (
        <Page
            title="Espace partenaire"
            subtitle="Encaissements, tableau de bord et catalogue arrivent bientôt."
        >
            <SessionNotice role="partner" />
        </Page>
    );
}
