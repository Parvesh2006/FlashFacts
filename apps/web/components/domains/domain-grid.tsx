import React from "react";
import { DomainStat } from "@/types/domain";
import { DomainCard } from "./domain-card";

interface DomainGridProps {
  domains: DomainStat[];
}

export function DomainGrid({ domains }: DomainGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-4">
      {domains.map((d) => (
        <DomainCard key={d.domain} domainStat={d} />
      ))}
    </div>
  );
}
