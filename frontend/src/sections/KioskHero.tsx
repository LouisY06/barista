import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const containerVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

export function KioskHero() {
  return (
    <section className="relative overflow-hidden text-white">
      <div className="absolute inset-0 bg-gradient-to-b from-[#101412] via-[#0B100E] to-[#080B0A]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(142,212,179,0.12),_transparent_55%)]" />

      <div className="relative mx-auto max-w-6xl px-4 py-20 md:py-28">
        <motion.div
          className="mx-auto max-w-3xl text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.6 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          <h1 className="text-4xl md:text-6xl font-semibold tracking-tight text-white">Try Our Kiosk</h1>
          <p className="mt-4 text-lg text-neutral-300/90">
            Order your perfect drink in seconds—customize size, sweetness, and toppings.
          </p>
        </motion.div>

        <motion.div
          className="relative mx-auto mt-10 max-w-4xl"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
        >
          <div className="absolute inset-x-4 -inset-y-8 rounded-[36px] bg-[radial-gradient(circle_at_top,_rgba(142,212,179,0.22),_transparent_65%)] blur-3xl opacity-70" />

          <div className="relative rounded-3xl border border-white/10 bg-white/10 p-6 sm:p-8 backdrop-blur-xl shadow-[0_15px_50px_rgba(0,0,0,0.35)]">
            <div className="grid gap-6 text-left sm:grid-cols-[1fr_auto] sm:items-center">
              <div className="space-y-2">
              <h3 className="text-base font-medium text-white/90">Launch the CAF-E Kiosk</h3>
                <p className="text-sm leading-relaxed text-neutral-200/85">
                  Customize your drink, adjust sweetness, and add premium toppings. Our online ordering mirrors the
                  in-store kiosk so your drink is ready when you arrive.
                </p>
              </div>

              <Link
                to="/kiosk"
                aria-label="Launch kiosk"
                className="group inline-flex items-center justify-center rounded-full px-6 py-3 text-base font-semibold bg-[#8ED4B3] text-[#0b1210] shadow-lg transition hover:bg-[#75c6a3] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8ED4B3] focus-visible:ring-offset-2 focus-visible:ring-offset-black"
              >
                Launch Kiosk
                <svg
                  className="ml-2 h-5 w-5 transition-transform duration-200 ease-out group-hover:translate-x-1"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path d="M9 18l6-6-6-6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

