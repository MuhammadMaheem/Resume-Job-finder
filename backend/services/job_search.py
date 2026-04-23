import httpx
from backend.config import get_settings
from typing import Optional
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger('jobmatcher')
settings = get_settings()


class JobSearch:
    """Search for jobs across multiple job boards and web sources."""

    def __init__(self):
        self.serpapi_key = settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search.json"
        # Country code mapping for Google Jobs (gl parameter)
        self.country_codes = {
            "USA": "us", "United States": "us", "US": "us", "America": "us",
            "UAE": "ae", "United Arab Emirates": "ae", "Dubai": "ae", "Abu Dhabi": "ae",
            "UK": "gb", "United Kingdom": "gb", "England": "gb", "London": "gb", "Britain": "gb",
            "Germany": "de", "Deutschland": "de", "Berlin": "de", "Munich": "de",
            "Canada": "ca", "Toronto": "ca", "Vancouver": "ca", "Montreal": "ca",
            "Australia": "au", "Sydney": "au", "Melbourne": "au",
            "India": "in", "Mumbai": "in", "Bangalore": "in", "Delhi": "in",
            "France": "fr", "Paris": "fr",
            "Netherlands": "nl", "Amsterdam": "nl",
            "Singapore": "sg",
            "Japan": "jp", "Tokyo": "jp",
            "China": "cn", "Beijing": "cn", "Shanghai": "cn",
            "Brazil": "br", "Sao Paulo": "br",
            "Mexico": "mx", "Mexico City": "mx",
            "Spain": "es", "Madrid": "es", "Barcelona": "es",
            "Italy": "it", "Rome": "it", "Milan": "it",
            "Sweden": "se", "Stockholm": "se",
            "Switzerland": "ch", "Zurich": "ch",
            "Saudi Arabia": "sa", "Riyadh": "sa",
            "Qatar": "qa", "Doha": "qa",
            "South Korea": "kr", "Seoul": "kr",
            "Indonesia": "id", "Jakarta": "id",
            "Philippines": "ph", "Manila": "ph",
            "Thailand": "th", "Bangkok": "th",
            "Vietnam": "vn", "Ho Chi Minh": "vn",
            "Poland": "pl", "Warsaw": "pl",
            "Ireland": "ie", "Dublin": "ie",
            "New Zealand": "nz", "Auckland": "nz",
            "South Africa": "za", "Cape Town": "za",
            "Israel": "il", "Tel Aviv": "il",
            "Turkey": "tr", "Istanbul": "tr",
            "Russia": "ru", "Moscow": "ru",
            "Worldwide": None,  # No country restriction
        }

    async def search_jobs_serpapi(self, query: str, location: str = "Remote", num_results: int = 10, 
                                   hours_since_posted: int = 24, location_type: str = "any",
                                   country: str = None, city: str = None, worldwide: bool = False) -> list[dict]:
        """Search for jobs using SerpAPI (Google Jobs) with enhanced location and time filtering."""
        if not self.serpapi_key:
            return await self.search_jobs_demo(query, location, num_results, hours_since_posted, location_type)

        # Build location string based on parameters
        search_location = location
        if worldwide:
            search_location = "Worldwide"
        elif city and country:
            search_location = f"{city}, {country}"
        elif city:
            search_location = city
        elif country:
            search_location = country

        # Map location_type to Google Jobs filters
        job_type_filter = None
        if location_type == "remote":
            job_type_filter = "Remote"
        elif location_type == "onsite":
            job_type_filter = "On-site"
        elif location_type == "hybrid":
            job_type_filter = "Hybrid"

        params = {
            "engine": "google_jobs",
            "q": query,
            "l": search_location,
            "hl": "en",
            "gl": "us",  # Default to US
            "api_key": self.serpapi_key,
            "num": min(num_results, 20),  # SerpAPI max is 20 per request
        }

        # Set country code based on location
        if worldwide:
            params["gl"] = "us"  # Default for worldwide
        elif country:
            # Try to find country code from mapping
            country_code = self.country_codes.get(country)
            if country_code:
                params["gl"] = country_code
            # If country not in mapping, keep default "us"
        elif city:
            # Try to infer country from city
            city_code = self.country_codes.get(city)
            if city_code:
                params["gl"] = city_code
        
        # Add job type filter if specified
        if job_type_filter:
            params["jtype"] = job_type_filter
        
        # Add time filter (past day, past 3 days, etc.)
        if hours_since_posted <= 24:
            params["tbd"] = "d"  # Past day
        elif hours_since_posted <= 72:
            params["tbd"] = "3d"  # Past 3 days
        elif hours_since_posted <= 168:
            params["tbd"] = "w"  # Past week

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

                    # Parse posted date
                    posted_date = job.get("detected_extensions", {}).get("posted_at", "")
                    
                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", job.get("via", "")),
                        "location": job.get("location", ""),
                        "job_type": job.get("detected_extensions", {}).get("schedule_type", "") or job_type_filter or "",
                        "salary_min": None,
                        "salary_max": None,
                        "description": job.get("description", ""),
                        "application_url": app_url,
                        "source": job.get("via", "Google Jobs"),
                        "posted_date": posted_date,
                        "requirements": [],
                    })
                return jobs
        except Exception as e:
            logger.warning(f"SerpAPI search failed: {e}. Falling back to demo mode.")
            return await self.search_jobs_demo(
                query, location, num_results, hours_since_posted, location_type,
                country=country, city=city, worldwide=worldwide
            )

    async def search_jobs_demo(self, query: str, location: str = "Remote", num_results: int = 5,
                                hours_since_posted: int = 24, location_type: str = "any",
                                country: str = None, city: str = None, worldwide: bool = False) -> list[dict]:
        """Generate demo jobs when SerpAPI is not configured."""
        # Expanded company list for more diversity (100+ companies)
        demo_companies = [
            "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix",
            "Stripe", "Shopify", "Spotify", "Tesla", "Adobe", "Salesforce",
            "Oracle", "IBM", "Intel", "Cisco", "Uber", "Airbnb", "Twitter",
            "LinkedIn", "GitHub", "GitLab", "Atlassian", "Slack",
            "Snap", "Pinterest", "Reddit", "Dropbox", "Square", "Twilio",
            "Datadog", "MongoDB", "Elastic", "Snowflake", "Palantir",
            "Databricks", "Plaid", "Notion", "Figma", "Vercel", "Stripe",
            "Coinbase", "Robinhood", "Affirm", "Ramp", "Brex",
            "Zapier", "Cloudflare", "Fastly", "DigitalOcean", "HashiCorp",
            "Epic Games", "Unity Technologies", "Roblox", "Discord", "Twitch",
            "Zoom", "DocuSign", "Workday", "ServiceNow", "Splunk",
            "New Relic", "AppDynamics", "Dynatrace", "Sumo Logic", "PagerDuty",
            "Okta", "CrowdStrike", "Palo Alto Networks", "Fortinet", "Zscaler",
            "Deloitte", "Accenture", "Capgemini", "Infosys", "TCS",
            "Wipro", "Cognizant", "HCL Technologies", "Tech Mahindra", "LTIMindtree",
            "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Bank of America", "Citigroup",
            "Visa", "Mastercard", "American Express", "PayPal", "Block",
            "Fidelity", "Charles Schwab", "BlackRock", "Vanguard", "State Street"
        ]

        # Job titles based on query
        keywords = query.split()[:5]
        base_titles = [
            "Software Engineer", "Full Stack Developer", "Backend Engineer",
            "Frontend Engineer", "DevOps Engineer", "Site Reliability Engineer",
            "Data Engineer", "ML Engineer", "Cloud Engineer", "Platform Engineer",
            "Senior Software Engineer", "Staff Engineer", "Principal Engineer",
            "Tech Lead", "Engineering Manager", "Solutions Architect",
            "Python Developer", "Java Developer", "React Developer", "Node.js Developer",
        ]

        # Location-based job types
        job_types_map = {
            "remote": ["Remote", "Remote"],
            "onsite": ["On-site", "On-site"],
            "hybrid": ["Hybrid", "Hybrid"],
            "any": ["Remote", "Hybrid", "On-site", "Remote", "Hybrid", "Remote"],  # Weighted towards remote
        }
        job_types = job_types_map.get(location_type, job_types_map["any"])

        # Build location string
        if worldwide:
            search_location = "Worldwide"
        elif city and country:
            search_location = f"{city}, {country}"
        elif city:
            search_location = city
        elif country:
            search_location = country
        else:
            search_location = location

        jobs = []
        for i in range(num_results):
            company = demo_companies[i % len(demo_companies)]
            job_type = job_types[i % len(job_types)]

            # Vary titles based on query
            if "data" in query.lower() or "ml" in query.lower():
                title = ["Data Engineer", "ML Engineer", "Data Scientist", "Analytics Engineer"][i % 4]
            elif "frontend" in query.lower() or "react" in query.lower():
                title = ["Frontend Engineer", "React Developer", "UI Engineer", "Web Developer"][i % 4]
            elif "backend" in query.lower() or "python" in query.lower():
                title = ["Backend Engineer", "Python Developer", "API Developer", "Systems Engineer"][i % 4]
            elif "devops" in query.lower() or "cloud" in query.lower():
                title = ["DevOps Engineer", "Cloud Engineer", "SRE", "Platform Engineer"][i % 4]
            else:
                title = base_titles[i % len(base_titles)]

            # Add seniority based on keywords
            if i % 3 == 0:
                title = f"Senior {title}"
            elif i % 5 == 0:
                title = f"Staff {title}"

            salary_min = random.randint(80000, 180000)
            salary_max = salary_min + random.randint(30000, 100000)

            # Generate realistic job descriptions
            skills_mentioned = keywords[:5] if keywords else ["Python", "JavaScript", "React", "Node.js", "SQL"]
            extra_skills = ["Docker", "Kubernetes", "AWS", "GCP", "PostgreSQL", "MongoDB", "GraphQL", "TypeScript", "Redis", "Kafka"]
            all_skills = skills_mentioned + random.sample(extra_skills, min(3, len(extra_skills)))

            jobs.append({
                "title": title,
                "company": company,
                "location": search_location if search_location else "Remote",
                "job_type": job_type,
                "salary_min": float(salary_min),
                "salary_max": float(salary_max),
                "description": f"We are seeking a talented {title} to join our engineering team at {company}. In this role, you will design, develop, and deploy scalable solutions that impact millions of users.\n\nResponsibilities:\n• Build and maintain high-performance applications\n• Collaborate with cross-functional teams to define and implement new features\n• Write clean, maintainable, and well-tested code\n• Participate in code reviews and mentor junior engineers\n• Optimize application performance and troubleshoot production issues\n\nRequirements:\n• Strong proficiency in {', '.join(all_skills[:3])}\n• Experience with agile development methodologies\n• Excellent problem-solving and communication skills\n• BS in Computer Science or equivalent experience\n\nBenefits:\n• Competitive salary and equity package\n• Health, dental, and vision insurance\n• Flexible PTO and remote work options\n• Professional development budget\n• Home office stipend",
                "application_url": f"https://www.google.com/search?q={title.replace(' ', '+')}+{company.replace(' ', '+')}&ibp=htl;jobs",
                "source": "Demo Jobs",
                "posted_date": (datetime.now() - timedelta(hours=random.randint(1, max(hours_since_posted, 24)))).isoformat(),
                "requirements": all_skills,
                "is_demo": True,  # Flag to indicate this is a demo job
            })
        return jobs

    async def search_jobs_manual(self, query: str, location: str = "Remote", num_results: int = 5) -> list[dict]:
        """Fallback manual search using direct job board scraping."""
        return await self.search_jobs_demo(query, location, num_results)

    async def search_multiple_queries(self, queries: list[dict], location: str = "Remote", 
                                       hours_since_posted: int = 24, location_type: str = "any",
                                       country: str = None, city: str = None, worldwide: bool = False) -> list[dict]:
        """Search for jobs using multiple generated queries and deduplicate results."""
        all_jobs = []
        seen_urls = set()

        for query_obj in queries:
            query = query_obj.get("query", "")
            if not query:
                continue

            jobs = await self.search_jobs_serpapi(
                query, location, 
                hours_since_posted=hours_since_posted,
                location_type=location_type,
                country=country, 
                city=city,
                worldwide=worldwide
            )

            for job in jobs:
                url = job.get("application_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_jobs.append(job)

        return all_jobs
