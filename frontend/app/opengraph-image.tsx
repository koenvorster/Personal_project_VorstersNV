import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'Koen Vorsters — Developer, Engineer & Innovator'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OGImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '60px 80px',
          background: 'linear-gradient(135deg, #0a0f1e 0%, #1e293b 100%)',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 80,
            height: 80,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #22c55e, #10b981)',
            marginBottom: 40,
            fontSize: 36,
            fontWeight: 700,
            color: 'white',
          }}
        >
          KV
        </div>
        <div style={{ fontSize: 64, fontWeight: 800, color: 'white', marginBottom: 16 }}>
          Koen Vorsters
        </div>
        <div style={{ fontSize: 28, color: '#94a3b8', marginBottom: 24 }}>
          Developer, Engineer & Innovator
        </div>
        <div style={{ fontSize: 20, color: '#64748b' }}>
          Full-stack · AI · IoT · DevOps
        </div>
        <div
          style={{
            width: 120,
            height: 4,
            borderRadius: 2,
            background: 'linear-gradient(90deg, #22c55e, #10b981)',
            marginTop: 40,
          }}
        />
      </div>
    ),
    { ...size }
  )
}
