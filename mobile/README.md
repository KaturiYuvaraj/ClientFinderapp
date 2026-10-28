# AI Client Finder — React Native Mobile Application

A cross-platform React Native mobile application for discovering real-time B2B clients, scoring lead opportunities, and managing outreach pipelines, built with **Expo** and styled with a **classic retro parchment aesthetic**.

---

## 📱 Features

- **Classic Retro Parchment Design**: Warm textured background, deep ruby/ink accents, typewriter labels, and stamp-like score badges.
- **Live OpenStreetMap (Overpass API) Data**: Full city administrative boundary lead discovery (not limited to small radius).
- **AI Opportunity Scoring**: Heuristic and rule-based evaluation detecting businesses without websites, low ratings, missing contacts, or high digital potential.
- **Pipeline Management**: Track leads through customizable stages (*New*, *Contacted*, *Interested*, *Follow Up*, *Converted*, *Not Interested*).
- **AI Outreach Message Generation**: Instant tailor-made pitch drafts based on business gaps and service offerings.
- **LAN-Ready & Expo Go Compatible**: Pre-configured with automatic Wi-Fi IP detection (`http://192.168.1.11:8000`) for seamless testing on physical devices.

---

## 🚀 Quick Start

### 1. Ensure Backend is Running
The backend must be running on your computer with `0.0.0.0` to accept connections from your phone on the local Wi-Fi:
```powershell
cd ..\backend
.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Expo Dev Server
```powershell
cd mobile
npx expo start --host lan
```

### 3. Open on Your Device
- **On Physical Mobile Phone (iOS / Android)**:
  1. Install **Expo Go** from Google Play Store or Apple App Store.
  2. Ensure your phone is connected to the same Wi-Fi network as this computer.
  3. Scan the QR code shown in your terminal with Expo Go (Android) or the Camera app (iOS).
- **In Web Browser**:
  - Visit `http://localhost:8081` in your browser.
- **On Android Emulator**:
  - Press `a` in the terminal running Expo.

---

## ⚙️ Connecting to Backend on Mobile Devices

When testing on a physical phone:
- The app automatically defaults to `http://192.168.1.11:8000` (your machine's local Wi-Fi IP).
- You can also tap **⚙️ Server** on the Login screen or visit the **Settings** tab at any time to:
  - Select quick presets (**📡 Wi-Fi IP**, **💻 Localhost**, or **🤖 Android Loopback** `10.0.2.2`).
  - Tap **Test Connection** to verify live backend health.

---

## 📂 Project Structure

```
mobile/
├── App.js                     # Root component: auth flow, bottom tabs, toast notifications
├── index.js                   # Expo entrypoint
├── package.json               # Dependencies & scripts
├── src/
│   ├── theme.js               # Retro design tokens (colors, radius, shadows, borders)
│   ├── services/
│   │   └── api.js             # API service with AsyncStorage token persistence
│   ├── components/
│   │   └── LeadCard.js        # Lead card, opportunity badge, AI pitch modal, status picker
│   └── screens/
│       ├── LoginScreen.js     # Sign in / Register, demo credentials, server IP switcher
│       ├── DashboardScreen.js # Lead KPIs, status breakdown bars, pull-to-refresh
│       ├── SearchScreen.js    # City + Category search, category chips, live OSM discovery
│       ├── LeadsScreen.js     # Saved pipeline list, search & status filters, edit/delete
│       └── SettingsScreen.js  # Server URL configuration, connection test, user profile
```

---

## 🔑 Demo Account
- **Email**: `yuvaraj@agency.com`
- **Password**: `password123`
*(Tap the "✦ Fill Demo Account" button on the login screen to autofill)*
