import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "Arvexo Radar",
  description: "Аналитика эффективности ИИ и лучшие практики компании.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
