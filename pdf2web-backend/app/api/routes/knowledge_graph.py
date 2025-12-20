"""Knowledge Graph API routes for auto-generated document navigation."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.document_store import document_store
from app.services.knowledge_graph_service import knowledge_graph_service

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


class KnowledgeGraphRequest(BaseModel):
    """Request for knowledge graph generation."""
    use_ai: bool = True
    max_nodes: Optional[int] = None
    entity_types: Optional[List[str]] = None


class KnowledgeGraphResponse(BaseModel):
    """Knowledge graph response."""
    document_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    structure: Dict[str, Any]
    metadata: Dict[str, Any]
    config: Dict[str, Any]
    layout_hints: Dict[str, Any]


class SimplifyRequest(BaseModel):
    """Request to simplify a knowledge graph."""
    max_nodes: int = 20
    entity_types: Optional[List[str]] = None


@router.post("/{document_id}/generate", response_model=KnowledgeGraphResponse)
async def generate_knowledge_graph(document_id: str, request: KnowledgeGraphRequest = KnowledgeGraphRequest()):
    """
    Generate a knowledge graph from document content.
    
    Analyzes document structure and semantics to create an interactive
    knowledge graph with entities (concepts, sections, people, dates)
    and relationships (references, builds-on, summarizes).
    
    Returns vis.js/Cytoscape.js compatible data for frontend rendering.
    """
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    graph = await knowledge_graph_service.generate_knowledge_graph(
        blocks=doc.blocks,
        document_id=document_id,
        use_ai=request.use_ai
    )
    
    if request.max_nodes or request.entity_types:
        graph = knowledge_graph_service.simplify_graph(
            graph,
            max_nodes=request.max_nodes or 50,
            entity_types=request.entity_types
        )
    
    document_store.set_knowledge_graph(document_id, graph)
    return graph


@router.get("/{document_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(document_id: str):
    """Get the generated knowledge graph for a document."""
    graph = document_store.get_knowledge_graph(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found. Generate it first using POST /generate")
    return graph


@router.post("/{document_id}/simplify", response_model=KnowledgeGraphResponse)
async def simplify_knowledge_graph(document_id: str, request: SimplifyRequest = SimplifyRequest()):
    """
    Simplify an existing knowledge graph for preview/approval.
    
    Reduces nodes to most important entities while preserving
    key relationships. Useful for co-design layer preview.
    """
    graph = document_store.get_knowledge_graph(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found. Generate it first.")
    
    simplified = knowledge_graph_service.simplify_graph(
        graph,
        max_nodes=request.max_nodes,
        entity_types=request.entity_types
    )
    return simplified


@router.get("/{document_id}/sidebar-data")
async def get_sidebar_data(document_id: str):
    """
    Get knowledge graph data formatted for sidebar navigation.
    
    Returns a simplified structure optimized for rendering
    a collapsible sidebar with clickable nodes.
    """
    graph = document_store.get_knowledge_graph(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    sidebar_data = {
        "document_id": document_id,
        "toc": graph["structure"]["toc"],
        "sections": [
            {
                "id": node["id"],
                "label": node["label"],
                "page": node["data"].get("page"),
                "block_id": node["data"].get("block_id"),
                "type": node["data"]["type"],
                "color": node["color"],
                "related": [
                    {"id": e["to"], "type": e["data"]["type"], "label": e["label"]}
                    for e in graph["edges"] if e["from"] == node["id"]
                ]
            }
            for node in graph["nodes"] if node["data"]["type"] == "section"
        ],
        "entities": {
            entity_type: [
                {"id": n["id"], "label": n["label"], "page": n["data"].get("page")}
                for n in graph["nodes"] if n["data"]["type"] == entity_type
            ]
            for entity_type in set(n["data"]["type"] for n in graph["nodes"])
        },
        "total_nodes": graph["metadata"]["total_nodes"],
        "total_edges": graph["metadata"]["total_edges"]
    }
    return sidebar_data


@router.get("/{document_id}/entity-types")
async def get_entity_types(document_id: str):
    """Get available entity types in the knowledge graph."""
    graph = document_store.get_knowledge_graph(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    return {
        "entity_types": graph["metadata"]["entity_types"],
        "relationship_types": graph["metadata"]["relationship_types"],
        "counts": {
            entity_type: len([n for n in graph["nodes"] if n["data"]["type"] == entity_type])
            for entity_type in graph["metadata"]["entity_types"]
        }
    }
