import type { Metadata } from "next";
import { Spectral } from "next/font/google";
import AppShell from "./components/AppShell/AppShell";
import Footer from "./components/Footer/Footer";
import SkipLink from "./components/SkipLink/SkipLink";
import "./global.css";

const spectral = Spectral({
    subsets: ["latin"],
    weight: ["400", "500", "600", "700"],
    variable: "--font-spectral",
});

export const metadata: Metadata = {
    title: "CartePro",
    description:
        "Votre budget CartePro à dépenser chez nos partenaires",
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
                <SkipLink />
                <AppShell>{children}</AppShell>
                <Footer />
            </body>
        </html>
    );
}
