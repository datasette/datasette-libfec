
export async function query(database: string, sql: string): Promise<any[]> {
  const params = new URLSearchParams();
  params.append("sql", sql);
  params.append("_shape", "array");
  return await fetch(`/${database}/-/query.json?${params.toString()}`).then((res) => res.json());
}