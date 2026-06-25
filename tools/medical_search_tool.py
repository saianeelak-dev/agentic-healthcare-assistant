from __future__ import annotations
from typing import Dict, Any, List, Tuple
import requests
from core.config import settings
from core.models import ToolTrace

class MedicalSearchTool:
    PUBMED_SEARCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    PUBMED_SUMMARY = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'

    def __init__(self) -> None:
        self.headers = {'User-Agent': settings.user_agent}

    def pubmed_search(self, query: str, retmax: int = 5) -> Tuple[List[Dict[str, Any]], ToolTrace]:
        params = {
            'db': 'pubmed',
            'term': query,
            'retmode': 'json',
            'retmax': retmax,
            'tool': settings.ncbi_tool,
            'email': settings.ncbi_email,
            'sort': 'relevance'
        }
        try:
            search_resp = requests.get(self.PUBMED_SEARCH, params=params, headers=self.headers, timeout=20)
            search_resp.raise_for_status()
            ids = search_resp.json().get('esearchresult', {}).get('idlist', [])
            if not ids:
                return [], ToolTrace('pubmed_search', {'query': query}, True, 'No PubMed results found')
            summary_resp = requests.get(self.PUBMED_SUMMARY, params={'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'json'}, headers=self.headers, timeout=20)
            summary_resp.raise_for_status()
            data = summary_resp.json().get('result', {})
            items = []
            for _id in ids:
                row = data.get(_id, {})
                items.append({'uid': _id, 'title': row.get('title', ''), 'pubdate': row.get('pubdate', ''), 'source': row.get('source', 'PubMed')})
            return items, ToolTrace('pubmed_search', {'query': query}, True, f'Retrieved {len(items)} PubMed summaries')
        except Exception as e:
            return [], ToolTrace('pubmed_search', {'query': query}, False, f'PubMed search failed: {e}')

    def who_stub(self, query: str):
        return [], ToolTrace('who_search', {'query': query}, False, 'WHO adapter placeholder: configure a WHO search endpoint if available')