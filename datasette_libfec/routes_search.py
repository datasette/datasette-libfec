from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional, List

from .router import router, check_permission
from .state import libfec_client

# Cache for search RPC clients (keyed by cycle)
search_clients = {}


class SearchParams(BaseModel):
    query: str
    cycle: Optional[int] = None
    limit: int = 100


class SearchResponse(BaseModel):
    status: str
    cycle: int
    query: str
    candidate_count: int
    committee_count: int
    candidates: List[dict]
    committees: List[dict]


@router.POST("/-/api/libfec/search", output=SearchResponse)
@check_permission()
async def search(datasette, request, params: Body[SearchParams]):
    """Search for candidates and committees using libfec search --rpc"""
    from .libfec_search_rpc_client import LibfecSearchRpcClient, RpcError

    cycle = params.cycle or 2026

    # Get or create search client for this cycle
    if cycle not in search_clients:
        try:
            client = LibfecSearchRpcClient(str(libfec_client.libfec_path), cycle)
            await client.start_process()
            search_clients[cycle] = client
        except Exception as e:
            return Response.json(
                {
                    "status": "error",
                    "message": f"Failed to start search process: {str(e)}",
                },
                status=500,
            )

    client = search_clients[cycle]

    try:
        result = await client.search_query(
            query=params.query, cycle=cycle, limit=params.limit
        )

        candidates = result["candidates"]
        committees = result["committees"]

        # Include principal campaign committees for matched candidates
        existing_committee_ids = {c["committee_id"] for c in committees}
        missing_committee_ids = []
        for candidate in candidates:
            pcc_id = candidate.get("principal_campaign_committee")
            if pcc_id and pcc_id not in existing_committee_ids:
                missing_committee_ids.append(pcc_id)
                existing_committee_ids.add(pcc_id)  # Avoid duplicates

        # Fetch missing principal committees
        for committee_id in missing_committee_ids:
            try:
                committee = await client.get_committee(committee_id, cycle)
                if committee:
                    committees.append(committee)
            except Exception:
                pass  # Skip if committee lookup fails

        return Response.json(
            {
                "status": "success",
                "cycle": result["cycle"],
                "query": result["query"],
                "candidate_count": result["candidate_count"],
                "committee_count": len(committees),
                "candidates": candidates,
                "committees": committees,
            }
        )

    except RpcError as e:
        return Response.json(
            {
                "status": "error",
                "message": f"Search error: {e.message}",
                "code": e.code,
            },
            status=500,
        )
    except Exception as e:
        return Response.json(
            {"status": "error", "message": f"Search failed: {str(e)}"}, status=500
        )
