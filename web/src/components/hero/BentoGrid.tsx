"use client";

import { useHeroData } from "./useHeroData";
import SearchCard from "./SearchCard";
import TypologyChipsCard from "./TypologyChipsCard";
import RiskGaugeCard from "./RiskGaugeCard";
import QuickLookupCard from "./QuickLookupCard";
import CriticalAlertsCard from "./CriticalAlertsCard";
import FlaggedVolumeCard from "./FlaggedVolumeCard";
import LatestDetectionCard from "./LatestDetectionCard";
import ModelEnsembleCard from "./ModelEnsembleCard";
import RocAucCard from "./RocAucCard";
import GridFloor from "./GridFloor";

export default function BentoGrid() {
  const { overview, topAlert, topAlertNarrative, distributions, evaluation, error } = useHeroData();

  return (
    <div className="relative mt-16 pb-24">
      <GridFloor />

      {error && (
        <div className="relative z-10 mb-4 text-xs font-mono text-[#B8562E]">
          Live data unavailable — start the API with `uvicorn api.main:app` ({error})
        </div>
      )}

      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-4 gap-4 auto-rows-[minmax(90px,auto)]">
        <div className="sm:col-span-1">
          <SearchCard />
        </div>
        <div className="sm:col-span-1 sm:row-span-2">
          <CriticalAlertsCard overview={overview} />
        </div>
        <div className="sm:col-span-1">
          <LatestDetectionCard topAlert={topAlert} narrative={topAlertNarrative} />
        </div>
        <div className="sm:col-span-1">
          <QuickLookupCard />
        </div>

        <div className="sm:col-span-1">
          <TypologyChipsCard />
        </div>
        <div className="sm:col-span-1">
          <RiskGaugeCard overview={overview} />
        </div>
        <div className="sm:col-span-1">
          <RocAucCard evaluation={evaluation} />
        </div>

        <div className="sm:col-span-2">
          <FlaggedVolumeCard overview={overview} />
        </div>
        <div className="sm:col-span-2">
          <ModelEnsembleCard distributions={distributions} />
        </div>
      </div>
    </div>
  );
}
