from pydantic import BaseModel
from datasette import Response
from datasette_plugin_router import Body
from typing import Optional, List

from .router import router
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
async def search(datasette, params: Body[SearchParams]):
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
            return Response.json({
                "status": "error",
                "message": f"Failed to start search process: {str(e)}"
            }, status=500)

    client = search_clients[cycle]

    try:
        result = await client.search_query(
            query=params.query,
            cycle=cycle,
            limit=params.limit
        )

        return Response.json({
            "status": "success",
            "cycle": result["cycle"],
            "query": result["query"],
            "candidate_count": result["candidate_count"],
            "committee_count": result["committee_count"],
            "candidates": result["candidates"],
            "committees": result["committees"]
        })

    except RpcError as e:
        return Response.json({
            "status": "error",
            "message": f"Search error: {e.message}",
            "code": e.code
        }, status=500)
    except Exception as e:
        return Response.json({
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }, status=500)
