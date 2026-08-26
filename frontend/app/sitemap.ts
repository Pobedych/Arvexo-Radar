import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://radar.arvexo.ru/",
      lastModified: new Date("2026-08-26"),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
