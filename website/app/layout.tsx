import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "IRIS AI — Your Private, Local AI Assistant",
  description:
    "The first truly private, local, personal AI assistant. Your own Iris, running on your machine. Zero data leaves your PC.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
