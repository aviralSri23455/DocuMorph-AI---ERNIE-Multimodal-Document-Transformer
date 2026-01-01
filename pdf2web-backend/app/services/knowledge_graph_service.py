"""Knowledge Graph Service for auto-generating navigable document graphs."""
import re
import json
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime
import httpx

from app.models.schemas import ContentBlock, ContentType
from app.config import settings


class KnowledgeGraphService:
    """Service for generating knowledge graphs from document content."""
    
    ENTITY_TYPES = ["concept", "person", "date", "location", "section", "table", "figure", "definition", "organization"]
    RELATIONSHIP_TYPES = ["references", "builds_on", "summarizes", "defines", "contains", "related_to", "precedes", "contrasts", "supports", "illustrates"]
    
    def __init__(self):
        self._http_client = None
        # Prioritize ERNIE (Novita AI) over DeepSeek to avoid payment issues
        self.api_key = settings.ernie_api_key
        self.api_url = settings.ernie_api_url
        self.model = settings.ernie_model
    
    @property
    def http_client(self):
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60)
        return self._http_client
    
    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def generate_knowledge_graph(self, blocks: List[ContentBlock], document_id: str, use_ai: bool = True) -> Dict[str, Any]:
        """Generate a knowledge graph from document content blocks."""
        logger.info(f"Generating knowledge graph for document {document_id}")
        structure = self._extract_document_structure(blocks)
        entities = await self._extract_entities(blocks, use_ai)
        relationships = await self._detect_relationships(blocks, entities, structure, use_ai)
        graph = self._build_graph(entities, relationships, structure, document_id)
        graph = self._add_layout_hints(graph)
        logger.info(f"Generated graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")
        return graph
    
    def _extract_document_structure(self, blocks: List[ContentBlock]) -> Dict[str, Any]:
        structure = {"sections": [], "hierarchy": {}, "toc": []}
        current_h1, current_h2 = None, None
        for block in blocks:
            if block.type == ContentType.HEADING:
                level = self._detect_heading_level(block.content)
                section = {"id": block.id, "title": block.content.strip(), "level": level, "page": block.page, "children": []}
                if level == 1:
                    current_h1, current_h2 = section, None
                    structure["sections"].append(section)
                elif level == 2 and current_h1:
                    current_h2 = section
                    current_h1["children"].append(section)
                elif level >= 3 and current_h2:
                    current_h2["children"].append(section)
                elif level >= 3 and current_h1:
                    current_h1["children"].append(section)
                else:
                    structure["sections"].append(section)
                structure["toc"].append({"id": block.id, "title": block.content.strip(), "level": level, "page": block.page})
        return structure
    
    def _detect_heading_level(self, content: str) -> int:
        content = content.strip()
        if content.startswith("# "): return 1
        elif content.startswith("## "): return 2
        elif content.startswith("### "): return 3
        if re.match(r'^(chapter|part)\s+\d+', content, re.IGNORECASE): return 1
        section_match = re.match(r'^(\d+\.)+\s*\w', content)
        if section_match: return min(content.count('.') + 1, 3)
        if len(content) < 50 and content.isupper(): return 1
        elif len(content) < 80: return 2
        return 3

    async def _extract_entities(self, blocks: List[ContentBlock], use_ai: bool) -> List[Dict[str, Any]]:
        entities, seen = [], set()
        for block in blocks:
            if block.type == ContentType.HEADING:
                entities.append({"id": f"entity_{block.id}", "type": "section", "label": block.content.strip()[:50], "full_text": block.content.strip(), "block_id": block.id, "page": block.page, "confidence": 0.95})
                seen.add(block.content.strip().lower())
            elif block.type == ContentType.TABLE:
                entities.append({"id": f"entity_table_{block.id}", "type": "table", "label": f"Table (Page {block.page})", "full_text": block.content[:200], "block_id": block.id, "page": block.page, "confidence": 0.9})
            for ent in self._extract_local_entities(block):
                if ent["label"].lower() not in seen:
                    entities.append(ent)
                    seen.add(ent["label"].lower())
        if use_ai and self.api_key:
            for ent in await self._extract_entities_with_ai(blocks):
                if ent["label"].lower() not in seen:
                    entities.append(ent)
                    seen.add(ent["label"].lower())
        return entities
    
    def _extract_local_entities(self, block: ContentBlock) -> List[Dict[str, Any]]:
        entities = []
        content = block.content
        date_patterns = [r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b']
        for pattern in date_patterns:
            for match in re.findall(pattern, content, re.IGNORECASE)[:3]:
                label = match if isinstance(match, str) else match[0]
                entities.append({"id": f"entity_date_{hash(label) % 10000}", "type": "date", "label": label, "full_text": label, "block_id": block.id, "page": block.page, "confidence": 0.8})
        return entities
    
    async def _extract_entities_with_ai(self, blocks: List[ContentBlock]) -> List[Dict[str, Any]]:
        entities = []
        combined = "\n\n".join([f"[{b.type.value.upper()}] {b.content[:500]}" for b in blocks[:20]])
        prompt = f"""Analyze this document and extract key entities.

Document content:
{combined[:4000]}

Extract entities: concept, person, organization, location, date.
Respond with JSON array: [{{"type": "concept", "label": "Machine Learning", "context": "discussed in section 2"}}]
Max 15 entities. JSON response:"""
        try:
            response = await self._call_ai(prompt)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                for i, ent in enumerate(json.loads(json_match.group())[:15]):
                    entities.append({"id": f"entity_ai_{i}_{hash(ent.get('label', '')) % 10000}", "type": ent.get("type", "concept"), "label": ent.get("label", "")[:50], "full_text": ent.get("label", ""), "context": ent.get("context", ""), "block_id": None, "page": None, "confidence": 0.85, "source": "ai"})
        except Exception as e:
            logger.warning(f"AI entity extraction failed: {e}")
        return entities
    
    async def _detect_relationships(self, blocks: List[ContentBlock], entities: List[Dict[str, Any]], structure: Dict[str, Any], use_ai: bool) -> List[Dict[str, Any]]:
        relationships = []
        for section in structure["sections"]:
            for child in section.get("children", []):
                relationships.append({"id": f"rel_{section['id']}_{child['id']}", "source": f"entity_{section['id']}", "target": f"entity_{child['id']}", "type": "contains", "label": "contains", "confidence": 0.95})
        section_entities = [e for e in entities if e["type"] == "section"]
        for i in range(len(section_entities) - 1):
            relationships.append({"id": f"rel_seq_{i}", "source": section_entities[i]["id"], "target": section_entities[i + 1]["id"], "type": "precedes", "label": "precedes", "confidence": 0.9})
        if use_ai and self.api_key:
            relationships.extend(await self._detect_relationships_with_ai(blocks, entities))
        return relationships
    
    async def _detect_relationships_with_ai(self, blocks: List[ContentBlock], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relationships = []
        entity_list = "\n".join([f"- {e['id']}: {e['type']} - {e['label']}" for e in entities[:15]])
        combined = "\n".join([b.content[:200] for b in blocks[:10]])
        prompt = f"""Analyze relationships between these document entities.

Entities:
{entity_list}

Document excerpt:
{combined[:2000]}

Identify 5-8 relationships. Types: references, builds_on, summarizes, defines, related_to.
Return ONLY a valid JSON array, no explanation:
[{{"source": "entity_id", "target": "entity_id", "type": "builds_on"}}]"""
        try:
            response = await self._call_ai(prompt)
            # Try to extract JSON array, handle truncated responses
            json_match = re.search(r'\[[\s\S]*?\]', response)
            if json_match:
                json_str = json_match.group()
                # Fix common truncation issues - ensure valid JSON
                try:
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to fix truncated JSON by closing brackets
                    json_str = re.sub(r',\s*$', '', json_str)  # Remove trailing comma
                    if not json_str.endswith(']'):
                        # Find last complete object
                        last_brace = json_str.rfind('}')
                        if last_brace > 0:
                            json_str = json_str[:last_brace+1] + ']'
                    parsed = json.loads(json_str)
                
                for i, rel in enumerate(parsed[:10]):
                    if rel.get("source") and rel.get("target"):
                        relationships.append({"id": f"rel_ai_{i}", "source": rel.get("source", ""), "target": rel.get("target", ""), "type": rel.get("type", "related_to"), "label": rel.get("type", "related_to").replace("_", " "), "reason": rel.get("reason", ""), "confidence": 0.75, "source_ai": True})
        except Exception as e:
            logger.warning(f"AI relationship detection failed: {e}")
        return relationships

    async def _call_ai(self, prompt: str) -> str:
        if not self.api_key:
            return "{}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": [{"role": "system", "content": "You are a document analysis assistant. Respond only with valid JSON."}, {"role": "user", "content": prompt}], "max_tokens": 1000, "temperature": 0.3}
        try:
            response = await self.http_client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return "{}"
    
    def _build_graph(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]], structure: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        type_colors = {"section": "#4e79a7", "concept": "#f28e2c", "person": "#e15759", "date": "#76b7b2", "location": "#59a14f", "table": "#edc949", "figure": "#af7aa1", "definition": "#ff9da7", "organization": "#9c755f"}
        type_shapes = {"section": "box", "concept": "ellipse", "person": "circle", "date": "diamond", "location": "triangle", "table": "square", "figure": "star", "definition": "hexagon", "organization": "database"}
        nodes, node_ids = [], set()
        for entity in entities:
            if entity["id"] in node_ids:
                continue
            node_ids.add(entity["id"])
            nodes.append({"id": entity["id"], "label": entity["label"][:30] + ("..." if len(entity["label"]) > 30 else ""), "title": entity.get("full_text", entity["label"]), "group": entity["type"], "color": type_colors.get(entity["type"], "#999999"), "shape": type_shapes.get(entity["type"], "dot"), "size": 25 if entity["type"] == "section" else 15, "font": {"size": 12}, "data": {"type": entity["type"], "block_id": entity.get("block_id"), "page": entity.get("page"), "confidence": entity.get("confidence", 0.5), "context": entity.get("context", "")}})
        rel_colors = {"contains": "#999999", "precedes": "#cccccc", "references": "#4e79a7", "builds_on": "#f28e2c", "summarizes": "#e15759", "defines": "#76b7b2", "related_to": "#59a14f", "contrasts": "#edc949", "supports": "#af7aa1", "illustrates": "#ff9da7"}
        edges, edge_ids = [], set()
        for rel in relationships:
            if rel["id"] in edge_ids or rel["source"] not in node_ids or rel["target"] not in node_ids:
                continue
            edge_ids.add(rel["id"])
            edges.append({"id": rel["id"], "from": rel["source"], "to": rel["target"], "label": rel.get("label", ""), "arrows": "to", "color": rel_colors.get(rel["type"], "#999999"), "dashes": rel["type"] in ["related_to", "contrasts"], "width": 2 if rel.get("confidence", 0.5) > 0.8 else 1, "data": {"type": rel["type"], "confidence": rel.get("confidence", 0.5), "reason": rel.get("reason", "")}})
        return {"document_id": document_id, "nodes": nodes, "edges": edges, "structure": structure, "metadata": {"generated_at": datetime.utcnow().isoformat(), "total_nodes": len(nodes), "total_edges": len(edges), "entity_types": list(set(e["type"] for e in entities)), "relationship_types": list(set(r["type"] for r in relationships))}, "config": {"physics": {"enabled": True, "solver": "forceAtlas2Based", "stabilization": {"iterations": 100}}, "interaction": {"hover": True, "tooltipDelay": 200, "navigationButtons": True}, "layout": {"hierarchical": {"enabled": False, "direction": "UD", "sortMethod": "directed"}}}}
    
    def _add_layout_hints(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        type_groups = {}
        for node in graph["nodes"]:
            node_type = node["data"]["type"]
            if node_type not in type_groups:
                type_groups[node_type] = []
            type_groups[node_type].append(node["id"])
        graph["layout_hints"] = {"groups": type_groups, "suggested_layout": "force-directed", "cluster_by_type": True}
        return graph
    
    def simplify_graph(self, graph: Dict[str, Any], max_nodes: int = 20, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simplify graph for preview/user approval."""
        nodes = graph["nodes"]
        if entity_types:
            nodes = [n for n in nodes if n["data"]["type"] in entity_types]
        def node_importance(n):
            type_priority = {"section": 0, "concept": 1, "table": 2}.get(n["data"]["type"], 3)
            return (type_priority, -n["data"].get("confidence", 0))
        nodes = sorted(nodes, key=node_importance)[:max_nodes]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in graph["edges"] if e["from"] in node_ids and e["to"] in node_ids]
        return {**graph, "nodes": nodes, "edges": edges, "metadata": {**graph["metadata"], "simplified": True, "original_nodes": graph["metadata"]["total_nodes"], "original_edges": graph["metadata"]["total_edges"]}}


knowledge_graph_service = KnowledgeGraphService()
