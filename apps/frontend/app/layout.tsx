import "./page.css";
import { ViewTransitions } from "next-view-transitions";
import Header from "@/components/header";

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <ViewTransitions>
            <html lang="en" className="h-full antialiased">
                <head>
                    <title>Kisa</title>
                </head>
                <body>
                    <Header />
                    {children}
                </body>
            </html>
        </ViewTransitions>
    );
}
