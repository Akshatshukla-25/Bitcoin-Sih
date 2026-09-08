import { Link2, Shuffle, Zap } from "lucide-react";

const TYPOLOGIES = [
  { icon: Link2, label: "Peel Chain" },
  { icon: Shuffle, label: "Mixer" },
  { icon: Zap, label: "Rapid Cash-out" },
];

export default function TypologyChipsCard() {
  return (
    <div className="bento-card p-4 flex flex-col gap-3 h-full">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Detected typologies</span>
      <div className="flex flex-col gap-2">
        {TYPOLOGIES.map(({ icon: Icon, label }) => (
          <div key={label} className="flex items-center gap-2 text-xs text-[#E8E6DE]">
            <Icon className="w-3.5 h-3.5 text-[#C8973B]" />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
