import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "TrustCheck",
  description: "Consensus-based online claim verification on GenLayer.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
