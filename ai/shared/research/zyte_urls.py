"""Search-URL builders for sites Zyte scrapes because no free structured API exists.

This is deliberately narrow in scope. General web/news search grounding is
Tavily/Exa's job (see tavily_provider.py / exa_provider.py) — they ARE proper
search APIs. Zyte's unique value, per the original spec, is scraping sites
that have no API at all: global patent offices, and specific pages once a
caller already knows the URL (a competitor's pricing page, a known
regulatory portal). Building URL guesses against Google/Bing's SERP HTML is
avoided here on purpose — it's fragile (JS-heavy, personalized, ToS-grey) and
Tavily/Exa already cover that ground properly.

The one general-purpose fallback included is DuckDuckGo's HTML endpoint
(html.duckduckgo.com), which is a plain server-rendered page built
specifically to be scraped without a browser — no API key, no JS — and is
the standard "no proper API for this" scraping target.
"""

from typing import List, NamedTuple
from urllib.parse import quote_plus


class SearchTarget(NamedTuple):
    """One (source label, URL) pair to scrape."""

    source: str
    url: str


def build_patent_search_urls(technology_concept: str) -> List[SearchTarget]:
    """Search-result URLs for the 4 global patent offices with no unified free API.

    Each URL is a plain search-results page. Espacenet and WIPO Patentscope
    render results client-side for some query shapes, so callers should pass
    `browser_html=True` to ZyteScraperTool.scrape_url for those two if the
    plain HTTP response comes back thin.
    """
    q = quote_plus(technology_concept)
    return [
        SearchTarget("google_patents", f"https://patents.google.com/?q=({q})"),
        SearchTarget("espacenet", f"https://worldwide.espacenet.com/patent/search?q={q}"),
        SearchTarget("wipo_patentscope", f"https://patentscope.wipo.int/search/en/result.jsf?query={q}"),
        SearchTarget("india_ip", f"https://search.ipindia.gov.in/IPOJournal/Journal/Patent?searchtext={q}"),
    ]


def build_duckduckgo_search_url(query: str, *, site: str = "") -> str:
    """DuckDuckGo's plain HTML search endpoint — no JS, no API key, meant for
    exactly this kind of scraping. Optionally scoped with a `site:` filter
    (e.g. site=".gov" for regulatory portals)."""
    full_query = f"{query} site:{site}" if site else query
    return f"https://html.duckduckgo.com/html/?q={quote_plus(full_query)}"


def build_regulatory_search_url(industry: str, region: str = "global") -> str:
    """Best-effort regulatory-portal search: DuckDuckGo scoped to .gov domains
    (or the region's typical government TLD) plus the industry keyword."""
    region_site_map = {
        "global": ".gov",
        "us": ".gov",
        "india": ".gov.in",
        "eu": ".europa.eu",
        "uk": ".gov.uk",
    }
    site = region_site_map.get(region.lower(), ".gov")
    return build_duckduckgo_search_url(f"{industry} regulations compliance", site=site)
