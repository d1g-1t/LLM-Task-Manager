import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '@/lib/providers';
import { Toaster } from 'sonner';

export const metadata: Metadata = {
  title: 'LLM Task Manager',
  description: 'Intelligent task manager with AI assistant — categorize, decompose and prioritize with LLM.',
  icons: { icon: '/favicon.svg' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="mx-auto max-w-6xl px-4 py-6 sm:py-10">{children}</div>
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
