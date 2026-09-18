import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import esES from 'antd/locale/es_ES'
import dayjs from 'dayjs'
import 'dayjs/locale/es'
import App from './App'
import './index.css'

// Configurar dayjs en español
dayjs.locale('es')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={esES}
      theme={{
        token: {
          colorPrimary: '#0891b2',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          colorInfo: '#0891b2',
          colorBgLayout: '#f0f4f8',
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          borderRadius: 12,
          borderRadiusLG: 16,
          borderRadiusSM: 8,
          boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
          boxShadowSecondary: '0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)',
        },
        components: {
          Card: {
            borderRadiusLG: 16,
          },
          Table: {
            headerBg: '#f0f4f8',
            headerColor: '#334155',
            borderRadius: 12,
          },
          Button: {
            borderRadius: 10,
            controlHeight: 40,
            fontWeight: 500,
          },
          Menu: {
            darkItemBg: 'transparent',
            darkItemSelectedBg: 'rgba(8, 145, 178, 0.25)',
            darkItemSelectedColor: '#22d3ee',
            darkItemHoverBg: 'rgba(255, 255, 255, 0.06)',
            itemBorderRadius: 10,
            itemMarginInline: 8,
          },
          Input: {
            borderRadius: 10,
            controlHeight: 42,
          },
          Select: {
            borderRadius: 10,
          },
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
