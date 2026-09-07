import LandingHero from "@/components/LandingHero";
import TrackRecord from "@/components/TrackRecord";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#05070B] text-[#E8E6DE]">
      <LandingHero />
      <TrackRecord />
    </main>
  );
}
