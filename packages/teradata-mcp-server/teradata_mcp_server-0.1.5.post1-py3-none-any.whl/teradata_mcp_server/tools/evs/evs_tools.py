import json
import logging

from teradatasql import TeradataConnection

from teradata_mcp_server.tools.evs_connect import get_evs
from teradata_mcp_server.tools.utils import create_response

logger = logging.getLogger("teradata_mcp_server")


#------------------ Do not make changes above  ------------------#


#================================================================
#  Enterprise Vector Store tools
#================================================================


def handle_evs_similarity_search(
    conn: TeradataConnection,
    question: str,
    top_k: int = 1,
    *args,
    **kwargs,
) -> str:
    """
    Enterprise Vector Store similarity search

    Arguments:
      question - the query string to search for
      top_k - number of top results to return

    Returns:
      ResponseType: formatted response with query results + metadata
    """
    logger.debug(f"EVS similarity_search: q='{question}', top_k={top_k}")
    vs = get_evs()
    try:
        results = vs.similarity_search(
            question=question,
            top_k=top_k,
            return_type="json",
        )
        return create_response(
            results,
            metadata={
                "tool_name": "evs_similarity_search",
                "question": question,
                "top_k": top_k,
            },
        )
    except Exception as e:
        logger.error(f"EVS similarity_search failed: {e}")
        return json.dumps({"status": "error", "message": str(e)})


