import { api } from "@/lib/api";
import { DomainStat } from "@/types/domain";

export async function getDomains(): Promise<DomainStat[]> {
  return api.get<DomainStat[]>("/api/v1/domains");
}
