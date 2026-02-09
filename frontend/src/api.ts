/**
 * Execute a SQL query against a Datasette database.
 * @param database - The database name to query
 * @param sql - The SQL query string (use :name for parameters)
 * @param parameters - Optional query parameters, passed as URL params (e.g., {id: "123"} for WHERE id = :id)
 */
export async function query(
  database: string,
  sql: string,
  parameters?: Record<string, string>
): Promise<any[]> {
  const params = new URLSearchParams();
  params.append("sql", sql);
  params.append("_shape", "array");
  if (parameters) {
    for (const [key, value] of Object.entries(parameters)) {
      params.append(key, value);
    }
  }
  return await fetch(`/${database}/-/query.json?${params.toString()}`).then((res) => res.json());
}