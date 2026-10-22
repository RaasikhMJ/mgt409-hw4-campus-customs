import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/session'
import { useBag } from '../cart/bag'
import { BagIcon } from './BagIcon'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
  { to: '/login', label: 'Log In', end: false },
  { to: '/create-account', label: 'Create Account', end: false },
]

export function NavBar() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const { shopper, logout } = useAuth()
  const bag = useBag()
  const links = shopper
    ? LINKS.filter((link) => link.to !== '/login' && link.to !== '/create-account')
    : LINKS

  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  return (
    <header className="nav">
      <a className="brand" href="/">
        <span className="brand-mark" aria-hidden="true">
          CC
        </span>
        <span>
          <strong>Campus Customs</strong>
          <small>New Haven</small>
        </span>
      </a>
      <div className="nav-end">
      <Link className="bag-mark" to="/cart" aria-label={`Open the bag, ${bag.count} queued`}>
        <BagIcon />
        <span>Bag</span>
        {bag.count > 0 && <span className="bag-count">{bag.count}</span>}
      </Link>
      <button
        className="nav-toggle"
        type="button"
        aria-expanded={open}
        aria-controls="site-nav"
        onClick={() => setOpen((value) => !value)}
      >
        {open ? 'Close' : 'Menu'}
      </button>
      <nav id="site-nav" className={open ? 'is-open' : ''} aria-label="Main">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              [
                'nav-link',
                link.label === 'Create Account' ? 'nav-join' : '',
                isActive ? 'is-active' : '',
              ]
                .filter(Boolean)
                .join(' ')
            }
          >
            {link.label}
          </NavLink>
        ))}
        {shopper && (
          <>
            <span className="nav-who">{shopper.firstName}</span>
            <button className="nav-link nav-join" type="button" onClick={() => void logout()}>
              Log out
            </button>
          </>
        )}
      </nav>
      </div>
    </header>
  )
}
