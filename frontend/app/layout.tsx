import Navbar from "./components/Navbar/Navbar";
import "./global.css";

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="fr">
            <body>
                <Navbar />
                {children}
            </body>
        </html>
    );
}