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
  return (
    <>
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
    </>
  )
}
