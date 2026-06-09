"use client";

import { useState } from "react";
import type { ApplicationSpace, Gap } from "@/lib/types";
import { ApplicationSpaceMap } from "./ApplicationSpaceMap";
import { GapInspector } from "./GapInspector";
import { SidebarFilters } from "./SidebarFilters";

export function ApplicationSpaceWorkspace({ space }: { space?: ApplicationSpace }) {
  const [selectedGap, setSelectedGap] = useState<Gap | undefined>(space?.gaps[0]);
  return (
    <div className="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)_360px]">
      <SidebarFilters />
      <ApplicationSpaceMap space={space} selectedGapId={selectedGap?.gap_id} onSelectGap={setSelectedGap} />
      <GapInspector gap={selectedGap} />
    </div>
  );
}
