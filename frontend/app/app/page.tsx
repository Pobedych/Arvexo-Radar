import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import "./radar.css";

import { RadarDashboard } from "../../components/RadarDashboard";
import { RADAR_SESSION_COOKIE, readRadarSession } from "../../lib/arvexo-auth";

export const metadata: Metadata = {
  title: "Дашборд — Arvexo Radar",
  description:
    "Рабочее пространство Arvexo Radar: классификация запросов к ИИ-агентам, карта сценариев, эффективность, ROI и лучшие практики.",
  alternates: { canonical: "/app" },
  robots: { index: false, follow: true },
};

export default async function AppPage() {
  const cookieStore = await cookies();
  const user = await readRadarSession(cookieStore.get(RADAR_SESSION_COOKIE)?.value);
  if (!user) redirect("/auth/login?returnTo=/app");
  return <RadarDashboard user={user} />;
}
