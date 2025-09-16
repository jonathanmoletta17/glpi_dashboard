import "./globals.css";
import { Providers } from "./providers";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "GLPI Dashboard",
  description: "Painel de métricas do Service Desk baseado na API do GLPI"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="dark">
        <Providers>
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
