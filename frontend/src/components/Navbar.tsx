import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react'
import './Navbar.css'

interface NavbarProps {
  currentPage: 'dashboard' | 'history' | 'insights'
  onNavigate: (page: 'dashboard' | 'history' | 'insights') => void
}

export default function Navbar({ currentPage, onNavigate }: NavbarProps) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <h1 className="navbar-title">CloudSense Platform</h1>
        <div className="navbar-buttons">
          <button 
            className={currentPage === 'dashboard' ? 'active' : ''}
            onClick={() => onNavigate('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={currentPage === 'history' ? 'active' : ''}
            onClick={() => onNavigate('history')}
          >
            History
          </button>
          <button 
            className={currentPage === 'insights' ? 'active' : ''}
            onClick={() => onNavigate('insights')}
          >
            Insights
          </button>
          
          <div className="auth-section">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="sign-in-btn">Sign In</button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </div>
        </div>
      </div>
    </nav>
  )
}
