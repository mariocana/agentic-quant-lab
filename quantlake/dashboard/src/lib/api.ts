// Client for the FastAPI dashboard server (src/quantlake/dashboard/server.py).
// Rebuilt: the original src/lib/ was dropped by the project's `lib/` gitignore rule.

export type Layer = "bronze" | "silver" | "gold";

export interface TableInfo {
  layer: Layer;
  name: string;
  path: string;
  rows: number | null;
  last_update: string | null;
  symbols: string[];
}

export interface SchemaField {
  column: string;
  dtype: string;
  numeric: boolean;
}

export type Row = Record<string, unknown>;

export interface DataPage {
  columns: string[];
  rows: Row[];
  page: number;
  page_size: number;
  total: number;
}

export interface Series {
  x: string;
  columns: string[];
  symbols: string[];
  points: Row[];
  total?: number;
}

export interface Bounds {
  min: string | null;
  max: string | null;
}

export interface StatRow {
  column: string;
  dtype: string;
  count: number | null;
  null_percentage: number | null;
  min: unknown;
  max: unknown;
  avg: unknown;
  std: unknown;
  q25: unknown;
  q50: unknown;
  q75: unknown;
  approx_unique: number | null;
}

export interface WorkflowSource {
  type?: string;
  modes?: string[];
  docs?: string;
}

export interface WorkflowNode {
  source?: string;
  from?: string[];
  grain?: string;
  partition?: string[];
  transforms?: string[];
  notes?: string;
}

export interface Workflow {
  sources: Record<string, WorkflowSource>;
  bronze: Record<string, WorkflowNode>;
  silver: Record<string, WorkflowNode>;
  gold: Record<string, WorkflowNode>;
}

type Params = Record<string, string | number | boolean | undefined | null>;

async function get<T>(path: string, params: Params = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const url = qs.toString() ? `${path}?${qs}` : path;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${url}`);
  return (await res.json()) as T;
}

const tablePath = (layer: Layer, name: string) =>
  `/api/tables/${layer}/${name.split("/").map(encodeURIComponent).join("/")}`;

const csv = (xs?: string[]) => (xs && xs.length ? xs.join(",") : undefined);

export const api = {
  layers: () => get<{ layers: Layer[] }>("/api/layers"),

  workflow: () => get<Workflow>("/api/workflow"),

  tables: (layer: Layer) => get<{ layer: Layer; tables: TableInfo[] }>(`/api/tables/${layer}`),

  schema: (layer: Layer, name: string) =>
    get<{ layer: Layer; name: string; schema: SchemaField[] }>(`${tablePath(layer, name)}/schema`),

  data: (
    layer: Layer,
    name: string,
    o: {
      symbols?: string[];
      page?: number;
      pageSize?: number;
      orderBy?: string;
      descending?: boolean;
      tsFrom?: string | null;
      tsTo?: string | null;
    } = {}
  ) =>
    get<DataPage>(`${tablePath(layer, name)}/data`, {
      symbols: csv(o.symbols),
      page: o.page,
      page_size: o.pageSize,
      order_by: o.orderBy,
      descending: o.descending,
      ts_from: o.tsFrom,
      ts_to: o.tsTo,
    }),

  series: (
    layer: Layer,
    name: string,
    o: {
      columns: string[];
      symbols?: string[];
      x?: string;
      maxPoints?: number;
      tsFrom?: string | null;
      tsTo?: string | null;
    }
  ) =>
    get<Series>(`${tablePath(layer, name)}/series`, {
      columns: csv(o.columns),
      symbols: csv(o.symbols),
      x: o.x,
      max_points: o.maxPoints,
      ts_from: o.tsFrom,
      ts_to: o.tsTo,
    }),

  bounds: (layer: Layer, name: string, symbol?: string | null) =>
    get<Bounds>(`${tablePath(layer, name)}/bounds`, { symbol: symbol ?? undefined }),

  stats: (
    layer: Layer,
    name: string,
    o: { symbols?: string[]; tsFrom?: string | null; tsTo?: string | null } = {}
  ) =>
    get<{ columns: string[]; stats: StatRow[] }>(`${tablePath(layer, name)}/stats`, {
      symbols: csv(o.symbols),
      ts_from: o.tsFrom,
      ts_to: o.tsTo,
    }),
};
