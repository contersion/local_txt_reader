import type { LibrarySourceKind } from "../types/api";


export interface ParsedLibraryBookId {
  sourceKind: LibrarySourceKind;
  entityId: number;
}

export function parseLibraryBookId(libraryBookId: string): ParsedLibraryBookId {
  if (!libraryBookId.includes(":")) {
    const entityId = Number(libraryBookId);
    if (!Number.isFinite(entityId) || entityId <= 0) {
      throw new Error(`无效的 libraryBookId：${libraryBookId}`);
    }
    return {
      sourceKind: "local",
      entityId,
    };
  }

  const [sourceKind, rawEntityId] = libraryBookId.split(":");
  const normalizedSourceKind = sourceKind === "online" ? "online" : "local";
  const entityId = Number(rawEntityId);

  if (!Number.isFinite(entityId) || entityId <= 0) {
    throw new Error(`无效的 libraryBookId：${libraryBookId}`);
  }

  return {
    sourceKind: normalizedSourceKind,
    entityId,
  };
}

export function buildLibraryBookId(sourceKind: LibrarySourceKind, entityId: number) {
  return `${sourceKind}:${entityId}`;
}
