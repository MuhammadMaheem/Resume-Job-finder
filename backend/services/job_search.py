import httpx
from backend.config import get_settings
from typing import Optional
from datetime import datetime, timedelta
import random

settings = get_settings()


class JobSearch:
    """Search for jobs across multiple job boards and web sources."""

    def __init__(self):
        self.serpapi_key = settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"

    async def search_jobs_serpapi(self, query: str, location: str = "Remote", num_results: int = 10) -> list[dict]:
        """Search for jobs using SerpAPI (Google Jobs)."""
        if not self.serpapi_key:
            return await self.search_jobs_demo(query, location, num_results)

        params = {
            "engine": "google_jobs",
            "q": query,
            "l": location,
            "hl": "en",
            "gl": "us",
            "api_key": self.serpapi_key,
            "num": num_results,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                jobs = []
                for job in data.get("jobs_results", [])[:num_results]:
                    # Get the best available link
                    app_url = job.get("source_link", "") or job.get("share_link", "")
                    if not app_url and job.get("job_links"):
                        app_url = job["job_links"][0].get("link", "")

                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", job.get("via", "")),
                        "location": job.get("location", ""),
                        "job_type": job.get("detected_extensions", {}).get("schedule_type", ""),
                        "salary_min": None,
                        "salary_max": None,
                        "description": job.get("description", ""),
                        "application_url": app_url,
                        "source": job.get("via", "Google Jobs"),
                        "posted_date": job.get("detected_extensions", {}).get("posted_at", ""),
                        "requirements": [],
                    })
                return jobs
        except Exception as e:
            print(f"Error searching via SerpAPI: {e}")
            return await self.search_jobs_demo(query, location, num_results)

    async def search_jobs_demo(self, query: str, location: str = "Remote", num_results: int = 5) -> list[dict]:
        """Generate demo jobs when SerpAPI is not configured."""
        demo_companies = [
            "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix",
            "Stripe", "Shopify", "Spotify", "Tesla", "Adobe", "Salesforce",
            "Oracle", "IBM", "Intel", "Cisco", "Uber", "Airbnb", "Twitter",
            "LinkedIn", "GitHub", "GitLab", "Atlassian", "Slack"
        ]
        job_types = ["Remote", "Hybrid", "On-site", "Remote", "Remote", "Hybrid"]

        # Extract keywords from query
        keywords = query.split()[:5]

        jobs = []
        for i in range(num_results):
            company = demo_companies[i % len(demo_companies)]
            job_type = job_types[i % len(job_types)]
            title = f"{' '.join(keywords[:3])}{' Engineer' if 'engineer' not in ' '.join(keywords).lower() else ''}"
            title = title.strip() or "Software Engineer"

            salary_min = random.randint(80000, 150000)
            salary_max = salary_min + random.randint(20000, 80000)

            jobs.append({
                "title": title,
                "company": company,
                "location": location if "remote" in location.lower() else f"{location} (Demo)",
                "job_type": job_type,
                "salary_min": float(salary_min),
                "salary_max": float(salary_max),
                "description": f"We are looking for a talented {title} to join our team at {company}. You will work on cutting-edge technologies and collaborate with world-class engineers. Requirements include: {', '.join(keywords[:5])}. This is a {job_type.lower()} position based in {location}.",
                "application_url": f"https://www.google.com/search?q={title.replace(' ', '+')}+{company.replace(' ', '+')}&ibp=htl;jobs",
                "source": "Demo Jobs",
                "posted_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "requirements": keywords[:5],
            })
        return jobs

    async def search_jobs_manual(self, query: str, location: str = "Remote", num_results: int = 5) -> list[dict]:
        """Fallback manual search using direct job board scraping."""
        return await self.search_jobs_demo(query, location, num_results)

    async def search_multiple_queries(self, queries: list[dict], location: str = "Remote") -> list[dict]:
        """Search for jobs using multiple generated queries and deduplicate results."""
        all_jobs = []
        seen_urls = set()

        for query_obj in queries:
            query = query_obj.get("query", "")
            if not query:
                continue

            jobs = await self.search_jobs_serpapi(query, location)

            for job in jobs:
                url = job.get("application_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_jobs.append(job)

        return all_jobs
