import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "District Status Checker",
  description: "Is anyone even working today? Check district status before you call.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-8 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-600">District Status Checker</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">Is anyone even working today?</h1>
            </div>
            <nav className="flex gap-3 text-sm text-slate-700">
              <Link className="rounded-full border border-slate-300 px-4 py-2 transition hover:border-slate-500" href="/">
                Check
              </Link>
              <Link className="rounded-full border border-slate-300 px-4 py-2 transition hover:border-slate-500" href="/admin">
                Admin
              </Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
