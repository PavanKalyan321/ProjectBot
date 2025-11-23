# Aviator Bot Dashboard - Next.js

Modern React dashboard for the Aviator Bot with real-time monitoring and AI predictions.

## Features

- **2-Column Split Layout**
  - **Left Iframe**: Bot controller with game multiplier display and manual controls
  - **Right Iframe**: Analytics panel with 16 ML model predictions and statistics

- **Real-Time Updates**
  - Socket.IO integration for live data streaming
  - Auto-refresh every 5 seconds
  - Live connection status indicator

- **ML Model Analytics**
  - All 16 model predictions displayed in grid
  - Ensemble prediction with confidence score
  - Top 3 models ranking
  - Individual model accuracy tracking

- **Trading Signals**
  - Trend analysis (UP/DOWN/NEUTRAL)
  - Trading signals (BET/SKIP/CAUTIOUS/OPPORTUNITY/WAIT)
  - Win rate and profit/loss tracking

- **Manual Controls**
  - Place bet with custom stake
  - Set target multiplier
  - Cancel bet
  - Pause/Resume bot
  - Live game multiplier display

## Project Structure

```
dashboard-nextjs/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Main dashboard page
│   │   └── layout.tsx        # Root layout
│   ├── components/
│   │   ├── Dashboard.tsx     # Main 2-column layout
│   │   ├── LeftIframe.tsx    # Bot controller
│   │   └── RightIframe.tsx   # Analytics panel
│   ├── lib/
│   │   ├── api.ts            # REST API client
│   │   └── socket.ts         # Socket.IO client
│   └── styles/
│       └── globals.css       # Global styles
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
└── next.config.ts
```

## Installation

1. **Install dependencies**
   ```bash
   cd dashboard-nextjs
   npm install
   ```

2. **Configure environment**
   - Edit `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:5001
   NEXT_PUBLIC_SOCKET_URL=http://localhost:5001
   ```

3. **Start Flask backend** (in another terminal)
   ```bash
   python run_dashboard.py --port 5001
   ```

4. **Start Next.js dev server**
   ```bash
   npm run dev
   ```

5. **Open dashboard**
   - Navigate to: http://localhost:3000

## Usage

### Dashboard Layout

The dashboard displays two iframes side-by-side:

**LEFT PANEL - Bot Controller:**
- Current multiplier in large, easy-to-read format
- Game status (AWAITING, RUNNING, CRASHED)
- Stake input field
- Target multiplier input
- Place Bet / Cancel Bet buttons
- Pause / Resume toggle

**RIGHT PANEL - Analytics:**
- Current round predictions from all 16 models
- Ensemble prediction with confidence percentage
- Trend indicator (↑ UP, ↓ DOWN, → NEUTRAL)
- Trading signal badge (BET, SKIP, CAUTIOUS, etc.)
- Live statistics:
  - Win Rate percentage
  - Profit/Loss amount
  - Total rounds played
- Top 3 performing models
- Line chart of last 10 rounds (prediction vs. actual)

### API Endpoints Used

The dashboard connects to these Flask backend endpoints:

```
GET  /api/current_round          # Current round with predictions
GET  /api/live_stats             # Win rate, P/L, total rounds
GET  /api/model_comparison       # All 16 models data
GET  /api/top_models             # Top 3 models ranking
GET  /api/recent_rounds?limit=20 # Last N rounds
GET  /api/trend_signal           # Trend and signal analysis
GET  /api/rules_status           # Game rules status
POST /api/cleanup                # Trigger data cleanup
```

### Socket.IO Events

Real-time updates via WebSocket:

```
# From Server
live_update      # Emits latest round data
stats_update     # Emits updated statistics
round_update     # Emits new round completion

# To Server
request_update   # Request latest data
place_bet        # Place a new bet
cancel_bet       # Cancel current bet
pause_bot        # Pause bot operation
resume_bot       # Resume bot operation
```

## Technology Stack

- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Real-Time**: Socket.IO Client
- **Backend**: Flask + Flask-SocketIO (Python)
- **Database**: Supabase PostgreSQL

## Development

### Build Project
```bash
npm run build
```

### Run Production Build
```bash
npm start
```

### Lint Code
```bash
npm run lint
```

## Deployment

### Frontend (Next.js)
Deploy to Vercel (recommended):
```bash
npm install -g vercel
vercel
```

Or build and deploy to any Node.js host:
```bash
npm run build
npm start
```

### Backend (Flask)
Keep Flask running on your server:
```bash
python run_dashboard.py --port 5001
```

### Environment Variables for Production
Set these in your deployment platform:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_SOCKET_URL=https://your-backend-url.com
```

## Features

### Real-Time Monitoring
- Live multiplier updates
- Instant prediction changes
- Real-time statistics
- Connection status indicator

### Analytics
- 16 ML model tracking
- Ensemble prediction accuracy
- Win/loss ratio
- Profit/loss tracking
- Performance charts

### User Controls
- Manual bet placement
- Stake customization
- Target multiplier adjustment
- Bot pause/resume
- Bet cancellation

### Responsive Design
- Optimized for desktop (primary)
- Tablet-friendly (stacks vertically)
- Mobile-accessible (iframes scroll)
- Dark theme for eye comfort

## Troubleshooting

### Dashboard shows "Loading..."
- Check Flask backend is running on port 5001
- Verify .env.local has correct API_URL
- Check browser console for error messages

### WebSocket connection fails
- Ensure Flask-SocketIO is enabled in backend
- Check CORS configuration in Flask
- Verify port 5001 is accessible

### Models not showing predictions
- Wait for current round to complete
- Check Flask backend has CSV data files
- Verify API endpoint `/api/model_comparison` works

### Chart not displaying
- Ensure recent_rounds data exists
- Check API response format matches expected structure
- Clear browser cache and reload

## API Documentation

See `../DASHBOARD_README.md` for complete Flask API documentation.

## License

MIT

## Author

Aviator Bot Development Team
