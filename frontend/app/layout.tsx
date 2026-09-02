import type { Metadata } from "next";
import { Spectral } from "next/font/google";
import AppShell from "./components/AppShell/AppShell";
import "./global.css";

const spectral = Spectral({
    subsets: ["latin"],
    weight: ["400", "500", "600", "700"],
    variable: "--font-spectral",
});

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
        <html lang="fr" className={spectral.variable}>
            <body>
                <AppShell>{children}</AppShell>
            </body>
        </html>
    );
}
