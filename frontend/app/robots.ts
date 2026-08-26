import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
    },
    sitemap: "https://radar.arvexo.ru/sitemap.xml",
    host: "https://radar.arvexo.ru",
  };
}
