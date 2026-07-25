export const metadata = {
  title: "Arvexo Radar",
  description: "Turn AI Conversations into Business Decisions.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
