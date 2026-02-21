import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import HomePage from './pages/HomePage'
import PaperPage from './pages/PaperPage'
import ComparisonPage from './pages/ComparisonPage'
import ProfilePage from './pages/ProfilePage'
import TrendsPage from './pages/TrendsPage'
import SubscriptionsPage from './pages/SubscriptionsPage'
import ArxivPushesPage from './pages/ArxivPushesPage'

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/paper/:paperId" element={<PaperPage />} />
        <Route path="/comparison" element={<ComparisonPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/trends" element={<TrendsPage />} />
        <Route path="/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/arxiv-pushes" element={<ArxivPushesPage />} />
      </Routes>
    </AppLayout>
  )
}
