import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const research = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/research' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.coerce.date(),
    updated: z.coerce.date().optional(),
    author: z.string().default('Agilentic Research'),
    tags: z.array(z.string()).default([]),
    category: z.string().default('Research Notes'),
    status: z.enum(['note', 'essay', 'brief', 'evergreen']).default('note'),
    featured: z.boolean().default(false),
    readingTime: z.string().optional()
  })
});

export const collections = { research };
