import { Link } from 'react-router-dom'

const productLinks = [
  { label: 'Soil Analysis', href: '/analyze' },
  { label: 'Crop Recommendations', href: '/crops' },
  { label: 'AI Assistant', href: '/assistant' },
  { label: 'Dashboard', href: '/dashboard' },
]

export default function Footer() {
  return (
    <footer className="bg-neutral-50 dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-8">
          {/* Brand */}
          <div className="max-w-sm">
            <Link to="/" className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-forest-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-forest-600/20">
                <span className="text-white text-lg">🌱</span>
              </div>
              <span className="text-lg font-bold tracking-tight text-neutral-900 dark:text-white font-display">
                AgroMind
              </span>
            </Link>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
              Intelligent soil analysis and smart crop recommendations. Grow better, harvest smarter.
            </p>
          </div>

          {/* Product — real routes only */}
          <nav aria-label="Product">
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-4 uppercase tracking-wider">
              Product
            </h3>
            <ul className="space-y-3">
              {productLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-forest-600 dark:hover:text-forest-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* Bottom */}
        <div className="mt-10 pt-6 border-t border-neutral-200 dark:border-neutral-800">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            © 2026 AgroMind. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
