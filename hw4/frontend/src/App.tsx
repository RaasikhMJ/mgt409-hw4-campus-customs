import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/session'
import { BagProvider } from './cart/bag'
import { Layout } from './components/Layout'
import { AboutPage } from './pages/AboutPage'
import { CartPage } from './pages/CartPage'
import { CreateAccountPage } from './pages/CreateAccountPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { ProductPage } from './pages/ProductPage'
import { ProductsPage } from './pages/ProductsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <BagProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="cart" element={<CartPage />} />
          <Route path="products/:productId" element={<ProductPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="create-account" element={<CreateAccountPage />} />
        </Route>
      </Routes>
      </BagProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
