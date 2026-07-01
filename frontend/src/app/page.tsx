import LandingNav from '@/components/landing/LandingNav'
import Hero from '@/components/landing/Hero'
import TrustStrip from '@/components/landing/TrustStrip'
import FeatureCards from '@/components/landing/FeatureCards'
import HowItWorks from '@/components/landing/HowItWorks'
import StatsBand from '@/components/landing/StatsBand'
import FAQ from '@/components/landing/FAQ'
import Testimonials from '@/components/landing/Testimonials'
import ClosingCTA from '@/components/landing/ClosingCTA'
import Footer from '@/components/landing/Footer'

export default function LandingPage() {
  // The whole app is one light editorial system (set on <body>); the boardroom
  // shares it so the Enter-the-boardroom hand-off has no seam.
  return (
    <div className="min-h-screen">
      <LandingNav />
      <main>
        <Hero />
        <TrustStrip />
        <FeatureCards />
        <HowItWorks />
        <StatsBand />
        <Testimonials />
        <FAQ />
        <ClosingCTA />
      </main>
      <Footer />
    </div>
  )
}
