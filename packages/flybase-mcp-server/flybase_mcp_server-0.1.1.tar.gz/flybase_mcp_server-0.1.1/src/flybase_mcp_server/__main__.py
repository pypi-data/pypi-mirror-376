from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

import csv
import re
import importlib.resources

# Initialize mcp server 
mcp = FastMCP("flybase")


# Constant
FLYBASE_API_BASE = "https://api.flybase.org/api/v1.0/"

### Helper functions

def is_flybase_id(identifier: str) -> bool:
    """Check if string looks like a FlyBase gene ID (FBgnxxxxxxx)."""
    return re.match(r"^FBgn\d{7}$", identifier) is not None

def load_gene_map() -> dict[str, str]:
    """Load GeneSymbol → FlyBaseID mapping from CSV."""
    gene_map = {}
    with importlib.resources.files("flybase_mcp_server.data").joinpath("gene_symbols_fbgn_ids.csv").open("r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            gene_map[row["gene_symbol"]] = row["fbgn_id"]
    return gene_map

GENE_MAP = load_gene_map()

def resolve_identifier(identifier: str) -> str | None:
    """Return FlyBase ID if input is FBgn or gene symbol."""
    if is_flybase_id(identifier):
        return identifier
    return GENE_MAP.get(identifier)

@mcp.tool()
async def get_flybase_gene_summary(gene_id: str) -> str | None:
    """Get gene summary from FlyBase

    Args: 
        identifier: Either FlyBase gene ID (FBgn) or a gene symbol.
    """

    fbgn_id = resolve_identifier(gene_id)
    if fbgn_id is None:
        return "Unable to find FlyBase ID. Try another gene symbol"

    url = f"{FLYBASE_API_BASE}gene/summaries/auto/{fbgn_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return data["resultset"]["result"][0]["summary"]
        except Exception:
            return None

@mcp.tool()
async def get_flybase_gene_ontology(gene_id: str, gene_ontology_domain: str) -> tuple[str, str] | str:
    """Get gene ontology (GO) slim for a gene from the specificed GO domain from Flybase
    
    Args:
    fbgn_id: FlyBase gene ID (FBgn)
    gene_ontology_domain: Gene ontology domain (Available values : biological_process, cellular_component, molecular_function)
    """

    fbgn_id = resolve_identifier(gene_id)
    if fbgn_id is None:
        return "Unable to find FlyBase ID. Try another gene symbol"

    url = f"{FLYBASE_API_BASE}ribbon/go/{gene_ontology_domain}/{fbgn_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if "resultset" not in data:
                return "'resultset' not in data: Unable to fetch information from FlyBase"
            
            data = data["resultset"]["result"][0]            
            go_slim_ids_order = ', '.join(data.get("slim_ids_order"))
            go_slim_names_order = ', '.join(data.get("slim_names_order"))
            return go_slim_ids_order, go_slim_names_order
        
        except Exception:
            return "Unable to fetch information"

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()





        