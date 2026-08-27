import { api } from "@/lib/api";
import { Source } from "@/types/source";

export async function getSources(enabledOnly?: boolean): Promise<Source[]> {
  return api.get<Source[]>("/api/v1/sources", { enabled: enabledOnly });
}
