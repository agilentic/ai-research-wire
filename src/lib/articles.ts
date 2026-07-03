import { getCollection } from 'astro:content';

export async function getArticles() {
  const articles = await getCollection('research');
  return articles
    .filter((entry) => !entry.id.startsWith('_'))
    .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export function articleHref(id: string) {
  return `/research/${id.replace(/\.(md|mdx)$/i, '')}/`;
}

export function allTags(articles: Awaited<ReturnType<typeof getArticles>>) {
  return [...new Set(articles.flatMap((article) => article.data.tags))].sort((a, b) => a.localeCompare(b));
}

export function allCategories(articles: Awaited<ReturnType<typeof getArticles>>) {
  return [...new Set(articles.map((article) => article.data.category))].sort((a, b) => a.localeCompare(b));
}
