import type { Metadata } from "next";
import AppShell from "./components/AppShell/AppShell";
import "./global.css";

export const metadata: Metadata = {
    title: "Ticket Tout",
    description:
        "Votre budget Ticket Tout à dépenser chez les partenaires du Ministère du Job et Bonheur.",
};

export const viewport = {
    width: "device-width",
    initialScale: 1,
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="fr">
            <body>
                <AppShell>{children}</AppShell>
            </body>
        </html>
    );
}
