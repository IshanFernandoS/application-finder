"use client";

import { useState } from "react";
import type { ApplicationSpace, Gap } from "@/lib/types";
import { ApplicationSpaceMap } from "./ApplicationSpaceMap";
import { GapInspector } from "./GapInspector";
import { SidebarFilters, emptyApplicationSpaceFilters, type ApplicationSpaceFilters } from "./SidebarFilters";

export function ApplicationSpaceWorkspace({ space }: { space?: ApplicationSpace }) {
  const [selectedGap, setSelectedGap] = useState<Gap | undefined>(space?.gaps[0]);
  const [filters, setFilters] = useState<ApplicationSpaceFilters>(emptyApplicationSpaceFilters);
  return (
    <div className="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)_360px]">
      <SidebarFilters space={space} filters={filters} onChange={setFilters} onReset={() => setFilters(emptyApplicationSpaceFilters)} />
      <ApplicationSpaceMap space={space} filters={filters} selectedGapId={selectedGap?.gap_id} onSelectGap={setSelectedGap} />
      <GapInspector gap={selectedGap} />
    </div>
  );
}
