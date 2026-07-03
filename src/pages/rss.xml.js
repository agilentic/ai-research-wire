import { getArticles, articleHref } from '../lib/articles';
export async function GET({ site }) {
  const articles = await getArticles();
  const base = site ?? new URL('https://agilentic.github.io');
  const items = articles.map((article) => `
    <item>
      <title><![CDATA[${article.data.title}]]></title>
      <description><![CDATA[${article.data.description}]]></description>
      <link>${new URL(`/ai-research-wire${articleHref(article.id)}`, base)}</link>
      <guid>${new URL(`/ai-research-wire${articleHref(article.id)}`, base)}</guid>
      <pubDate>${article.data.date.toUTCString()}</pubDate>
    </item>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>AI Research Wire</title><link>${new URL('/ai-research-wire/', base)}</link><description>AI research notes and essays.</description>${items}</channel></rss>`, { headers: { 'Content-Type': 'application/xml' } });
}
