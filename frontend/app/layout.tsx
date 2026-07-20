import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

// Carregadas via <link> (não via next/font/google) de propósito: next/font
// baixa os arquivos de fonte em build-time, o que quebra em ambientes de
// CI/CD com rede restrita (ex: sem acesso a fonts.googleapis.com). Um
// <link> resolve no browser do usuário final, sem essa dependência de rede
// no momento do build.
export const metadata: Metadata = {
  title: "STEMS AI — Separação de stems com IA",
  description: "Separe vocal, bateria, baixo, guitarra e piano de qualquer música com IA. Grátis e open-source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body bg-base-bg text-slate-100 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
