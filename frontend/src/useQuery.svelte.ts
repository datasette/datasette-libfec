export class QueryResponse<T> {
  data = $state<T>();
  error = $state<string>();
  isLoading = $state(false);
  refetch?: () => Promise<void>;
}

export function useQuery<T>(queryFn: () => Promise<T>) {
  const resp = new QueryResponse<T>();

  resp.refetch = async function () {
    resp.isLoading = true;
    try {
      resp.data = await queryFn();
      resp.error = undefined;
    } catch (err) {
      resp.error = err instanceof Error ? err.message : String(err);
      resp.data = undefined;
    }
    resp.isLoading = false;
  };

  resp.refetch();

  return resp;
}
