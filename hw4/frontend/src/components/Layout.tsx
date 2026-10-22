import { Outlet } from 'react-router-dom'
import { MatchProvider } from '../rack/matches'
import { BudgetBar } from './BudgetBar'
import { MatchRack } from './MatchRack'
import { NavBar } from './NavBar'
import { SiteFooter } from './SiteFooter'
import { StylistChat } from './StylistChat'

export function Layout() {
  return (
    <MatchProvider>
      <NavBar />
      <BudgetBar />
      <MatchRack />
      <main>
        <Outlet />
      </main>
      <SiteFooter />
      <StylistChat />
    </MatchProvider>
  )
}
