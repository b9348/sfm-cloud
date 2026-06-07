export default function Home() {
  return (
    <main style={{ padding: '40px', fontFamily: 'system-ui' }}>
      <h1>SFM Cloud API</h1>
      <p>Backend API for SFM Cloud</p>

      <h2>Authentication Endpoints:</h2>
      <ul>
        <li>POST /api/auth/register - User registration</li>
        <li>POST /api/auth/login - User login</li>
      </ul>

      <h2>Mod Endpoints:</h2>
      <ul>
        <li>GET /api/mods/list?lang=en&page=1&limit=20 - List all mods</li>
        <li>GET /api/mods/{id}?lang=en - Get mod details</li>
        <li>POST /api/mods/create - Create new mod (requires auth)</li>
      </ul>

      <h2>User Endpoints:</h2>
      <ul>
        <li>GET /api/user/profile - Get user profile (requires auth)</li>
      </ul>

      <h2>Supported Languages:</h2>
      <p>zh (Chinese), en (English), ja (Japanese), ko (Korean), ru (Russian), fr (French), de (German)</p>
    </main>
  )
}
