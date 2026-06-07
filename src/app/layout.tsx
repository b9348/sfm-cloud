export const metadata = {
  title: 'SFM Cloud API',
  description: 'Backend API for SFM Cloud',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
