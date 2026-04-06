from groq import Groq
from config import get_settings
import json
from typing import Optional

settings = get_settings()


class GroqAI:
    """Groq AI service for LLM-based resume analysis and job matching."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"

    def analyze_resume(self, resume_text: str) -> Optional[dict]:
        """Analyze resume text and extract structured information."""
        prompt = f"""
You are an expert resume analyzer. Analyze the following resume and extract structured information in JSON format.

Extract:
- skills: list of all technical and soft skills
- experience: list of work experiences with title, company, duration, and key responsibilities
- education: list of degrees with institution, field, and year
- certifications: list of certifications
- summary: brief professional summary
- years_of_experience: estimated total years of experience
- seniority_level: one of "entry", "mid", "senior", "lead", "executive"
- industries: industries the candidate has worked in
- key_achievements: notable achievements or metrics

Resume text:
{resume_text[:8000]}

Respond ONLY with valid JSON. No extra text.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return None
        except Exception as e:
            print(f"Error analyzing resume: {e}")
            return None

    def search_jobs_query(self, resume_analysis: dict, location: str = "Remote") -> str:
        """Generate optimized job search queries based on resume analysis."""
        skills = resume_analysis.get("skills", [])
        seniority = resume_analysis.get("seniority_level", "")
        industries = resume_analysis.get("industries", [])

        prompt = f"""
Based on this resume analysis, generate 3 specific job search queries that would find the best matching jobs.

Skills: {', '.join(skills[:10])}
Seniority: {seniority}
Industries: {', '.join(industries)}
Preferred location: {location}

Return a JSON array with 3 search query objects:
[
  {{"query": "specific search query", "focus": "what this query focuses on"}}
]

Respond ONLY with valid JSON.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1024,
            )
            content = response.choices[0].message.content
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                queries = json.loads(content[start:end])
                return queries
            return [{"query": f"{seniority} {' '.join(skills[:5])} jobs {location}", "focus": "general"}]
        except Exception as e:
            print(f"Error generating search queries: {e}")
            return [{"query": f"{' '.join(skills[:5])} jobs", "focus": "general"}]

    def match_job_to_resume(self, job_description: str, resume_analysis: dict) -> Optional[dict]:
        """Calculate how well a job matches with a resume."""
        prompt = f"""
You are an expert job matcher. Analyze how well this job description matches the candidate's resume.

JOB DESCRIPTION:
{job_description[:4000]}

CANDIDATE PROFILE:
Skills: {', '.join(resume_analysis.get('skills', []))}
Experience: {resume_analysis.get('years_of_experience', 'N/A')} years
Seniority: {resume_analysis.get('seniority_level', 'N/A')}
Industries: {', '.join(resume_analysis.get('industries', []))}

Provide a JSON response with:
- match_score: 0-100 score of how well this job matches the candidate
- match_reasons: list of 3-5 reasons why this is a good match
- missing_skills: list of required skills the candidate might be missing
- strong_points: list of areas where the candidate strongly matches
- recommendation: "highly_recommended", "recommended", "consider", or "not_recommended"

Respond ONLY with valid JSON.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1,
                max_tokens=2048,
            )
            content = response.choices[0].message.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return None
        except Exception as e:
            print(f"Error matching job: {e}")
            return None

    def generate_cover_letter(self, job_description: str, resume_analysis: dict, company: str, title: str) -> Optional[str]:
        """Generate a customized cover letter."""
        prompt = f"""
Write a professional, compelling cover letter for the following position.

POSITION: {title} at {company}

JOB DESCRIPTION:
{job_description[:3000]}

CANDIDATE PROFILE:
Skills: {', '.join(resume_analysis.get('skills', []))}
Experience: {resume_analysis.get('years_of_experience', 'N/A')} years
Seniority: {resume_analysis.get('seniority_level', 'N/A')}
Key Achievements: {', '.join(resume_analysis.get('key_achievements', []))}

Write a cover letter that:
1. Opens with enthusiasm for the specific role and company
2. Highlights the most relevant experience and achievements
3. Shows understanding of the company's needs
4. Demonstrates specific value the candidate would bring
5. Closes with a call to action

Make it personalized, specific, and avoid generic phrases. Keep it to 3-4 paragraphs.
Return ONLY the cover letter text, no additional formatting.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return None

    def suggest_resume_improvements(self, resume_analysis: dict, target_jobs: list) -> Optional[dict]:
        """Suggest improvements to the resume based on target jobs."""
        prompt = f"""
Analyze the candidate's resume and suggest improvements to better match these target jobs.

CANDIDATE PROFILE:
Skills: {', '.join(resume_analysis.get('skills', []))}
Experience: {resume_analysis.get('years_of_experience', 'N/A')} years
Seniority: {resume_analysis.get('seniority_level', 'N/A')}

TARGET JOB TITLES:
{', '.join(target_jobs[:5])}

Provide a JSON response with:
- missing_keywords: list of keywords/skills to add to resume
- skill_gaps: list of skills to learn/improve
- suggestions: list of 5 specific resume improvement tips
- recommended_certifications: list of certifications that would help
- trending_skills: list of trending skills in their field to consider learning

Respond ONLY with valid JSON.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.2,
                max_tokens=2048,
            )
            content = response.choices[0].message.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return None
        except Exception as e:
            print(f"Error suggesting improvements: {e}")
            return None

    def generate_interview_questions(self, job_description: str, title: str, company: str, candidate_profile: str) -> list[dict]:
        """Generate interview questions based on job description and candidate profile."""
        prompt = f"""
Generate interview questions for the following position and candidate.

POSITION: {title} at {company}

JOB DESCRIPTION:
{job_description[:3000]}

{candidate_profile}

Generate 15 interview questions across 3 categories:
1. Technical (5 questions) - about skills, tools, and technologies
2. Behavioral (5 questions) - about past experiences, teamwork, problem-solving
3. Company-specific (5 questions) - about this specific company and role

For each question provide a suggested good answer.

Respond ONLY with valid JSON in this format:
[
  {{"category": "technical", "question": "What is...", "suggested_answer": "A good answer..."}},
  ...
]
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.5,
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def generate_networking_suggestions(self, company: str, title: str, description: str) -> list[dict]:
        """Generate networking suggestions for people to connect with at the target company."""
        prompt = f"""
Suggest networking contacts for a job application.

TARGET: {title} at {company}

JOB DESCRIPTION (abbreviated):
{description[:1000]}

Suggest 5 types of people the candidate should try to connect with at this company:
1. Hiring managers or team leads in the relevant department
2. Senior engineers or specialists in the same field
3. Recruiters who specialize this area
4. Alumni from similar backgrounds now at this company
5. People in adjacent roles who can provide insights

For each suggestion provide:
- company: the company name
- role: the type of role this person might have
- linkedin_url: a Google search URL to find such people on LinkedIn
- suggestion: why and how to approach them

Respond ONLY with valid JSON:
[
  {{"company": "Company", "role": "Engineering Manager", "linkedin_url": "https://www.linkedin.com/search/results/people/?keywords=...", "suggestion": "Connect and ask about..."}}
]
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=2048,
            )
            content = response.choices[0].message.content
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return []
        except Exception as e:
            print(f"Error generating networking: {e}")
            return []

    def rewrite_resume_for_job(self, resume_text: str, job_description: str, title: str, company: str) -> dict:
        """Rewrite a resume tailored to a specific job."""
        prompt = f"""
Rewrite this resume to be perfectly tailored for the following job.

TARGET JOB: {title} at {company}

JOB DESCRIPTION:
{job_description[:3000]}

ORIGINAL RESUME:
{resume_text[:4000]}

Rules:
1. Keep the same structure and truthful information
2. Reorder skills to highlight what the job requires most
3. Rewrite bullet points to use keywords from the job description
4. Add a targeted professional summary at the top
5. Emphasize relevant experience and achievements

Respond with JSON:
{{
  "summary": "The new targeted professional summary",
  "tailored_text": "The full rewritten resume text"
}}
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return {"summary": "", "tailored_text": ""}
        except Exception as e:
            print(f"Error rewriting resume: {e}")
            return {"summary": "", "tailored_text": ""}
