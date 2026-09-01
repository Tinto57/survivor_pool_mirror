"use client";

import Page from "../components/Page/Page";
import SessionNotice from "../components/SessionNotice/SessionNotice";

export default function AdminHome() {
    return (
        <Page
            title="Espace Ministère"
            subtitle="Validation des partenaires, abondements et Coup de cœur du Ministre arrivent bientôt."
        >
            <SessionNotice role="admin" />
        </Page>
    );
}
