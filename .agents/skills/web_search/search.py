import urllib.parse
from typing import List
from schemas import Resource

# Allowed and blocked domains for validation
ALLOWED_DOMAINS = [
    "docs.python.org", "wikipedia.org", "coursera.org", "edx.org",
    "khanacademy.org", "youtube.com", "mit.edu", "harvard.edu",
    "stanford.edu", "w3schools.com", "developer.mozilla.org",
    "geeksforgeeks.org", "tutorialspoint.com", "medium.com"
]

BLOCKED_DOMAINS = [
    "reddit.com", "quora.com", "4chan.org", "hackforums.net",
    "torrent", "pirate", "crack", "warez", "spam"
]

def filter_url(url: str) -> bool:
    """Verifies that a URL comes from allowed sources and not blocked sources."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    
    # Check if domain matches any blocked keyword or domain
    for blocked in BLOCKED_DOMAINS:
        if blocked in domain or blocked in parsed.path:
            return False
            
    # Check if domain ends with any allowed domain name
    for allowed in ALLOWED_DOMAINS:
        if domain == allowed or domain.endswith("." + allowed):
            return True
            
    # If it is an educational domain, allow it
    if domain.endswith(".edu") or domain.endswith(".gov") or domain.endswith(".org"):
        return True
        
    return False

# Custom lookup for known skills to return realistic educational resources
KNOW_SKILL_RESOURCES = {
    "law": [
        Resource(
            title="Introduction to American Law (Coursera / Penn Law)",
            url="https://www.coursera.org/learn/american-law",
            type="Course"
        ),
        Resource(
            title="Legal Profession and Ethics Guides (Wikipedia)",
            url="https://en.wikipedia.org/wiki/Lawyer",
            type="Documentation"
        ),
        Resource(
            title="Fundamentals of Legal Writing and Argumentation (YouTube)",
            url="https://www.youtube.com/watch?v=mock_law_writing",
            type="Video"
        )
    ],
    "cooking": [
        Resource(
            title="Cooking Techniques & Culinary Arts Course (edX)",
            url="https://www.edx.org/course/cooking-basics",
            type="Course"
        ),
        Resource(
            title="Culinary Fundamentals & Kitchen Safety Guides (Wikipedia)",
            url="https://en.wikipedia.org/wiki/Culinary_arts",
            type="Documentation"
        ),
        Resource(
            title="Mastering Basic Knife Skills & Techniques (YouTube)",
            url="https://www.youtube.com/watch?v=mock_cooking_skills",
            type="Video"
        )
    ],
    "gardening": [
        Resource(
            title="Horticulture and Home Gardening Specialization (Coursera)",
            url="https://www.coursera.org/learn/gardening",
            type="Course"
        ),
        Resource(
            title="Soil Preparation, Planting, and Organic Gardening (Wikipedia)",
            url="https://en.wikipedia.org/wiki/Gardening",
            type="Documentation"
        ),
        Resource(
            title="Beginner Gardening & Planting Walkthrough (YouTube)",
            url="https://www.youtube.com/watch?v=mock_gardening_basics",
            type="Video"
        )
    ],
    "history": [
        Resource(
            title="World History: Modern Era Specialization (Coursera)",
            url="https://www.coursera.org/learn/world-history",
            type="Course"
        ),
        Resource(
            title="Outline of World History & Historical Records (Wikipedia)",
            url="https://en.wikipedia.org/wiki/History_of_the_world",
            type="Documentation"
        ),
        Resource(
            title="World History Crash Course (YouTube)",
            url="https://www.youtube.com/watch?v=mock_world_history",
            type="Video"
        )
    ],
    "journalism": [
        Resource(
            title="Introduction to Journalism Course (Coursera)",
            url="https://www.coursera.org/learn/journalism",
            type="Course"
        ),
        Resource(
            title="SPJ Code of Ethics (Society of Professional Journalists)",
            url="https://www.spj.org/ethicscode.asp",
            type="Documentation"
        ),
        Resource(
            title="Basic News Writing Tutorials (YouTube)",
            url="https://www.youtube.com/watch?v=mock_journalism_basics",
            type="Video"
        )
    ],
    "python": [
        Resource(
            title="Python Tutorial (Official Python Documentation)",
            url="https://docs.python.org/3/tutorial/index.html",
            type="Documentation"
        ),
        Resource(
            title="Programming for Everybody: Python (Coursera)",
            url="https://www.coursera.org/specializations/python",
            type="Course"
        ),
        Resource(
            title="Python for Beginners - Full Course (YouTube)",
            url="https://www.youtube.com/watch?v=mock_python_beginners",
            type="Video"
        )
    ],
    "retail": [
        Resource(
            title="Retail Management Course (edX)",
            url="https://www.edx.org/course/retail-management",
            type="Course"
        ),
        Resource(
            title="Introduction to Retail Operations (Wikipedia)",
            url="https://en.wikipedia.org/wiki/Retail",
            type="Documentation"
        ),
        Resource(
            title="Retail Customer Service Guide (YouTube)",
            url="https://www.youtube.com/watch?v=mock_retail_service",
            type="Video"
        )
    ],
    "marketing": [
        Resource(
            title="Digital Marketing Specialization (Coursera)",
            url="https://www.coursera.org/specializations/digital-marketing",
            type="Course"
        ),
        Resource(
            title="Google Digital Garage: Marketing",
            url="https://www.coursera.org/learn/google-digital-marketing-ecommerce",
            type="Course"
        ),
        Resource(
            title="What is Marketing? Fundamentals (YouTube)",
            url="https://www.youtube.com/watch?v=mock_marketing_intro",
            type="Video"
        )
    ],
    "data analysis": [
        Resource(
            title="Google Data Analytics Professional Certificate",
            url="https://www.coursera.org/professional-certificates/google-data-analytics",
            type="Course"
        ),
        Resource(
            title="Pandas Documentation (Data Analysis Library)",
            url="https://pandas.pydata.org/docs/",
            type="Documentation"
        ),
        Resource(
            title="Data Analysis for Beginners (YouTube)",
            url="https://www.youtube.com/watch?v=mock_data_analysis",
            type="Video"
        )
    ]
}

def search_resources(query: str) -> List[Resource]:
    """Retrieves high-quality, beginner-friendly educational resources for a skill."""
    query_clean = query.strip().lower()
    
    # Check if we have predefined resources for the skill
    for known_skill, resources in KNOW_SKILL_RESOURCES.items():
        if known_skill in query_clean or query_clean in known_skill:
            return resources
            
    # Fallback dynamic resource generation using allowed sources
    query_encoded = urllib.parse.quote(query)
    fallback_resources = [
        Resource(
            title=f"Learn {query} from Scratch (Coursera)",
            url=f"https://www.coursera.org/search?query={query_encoded}",
            type="Course"
        ),
        Resource(
            title=f"{query} Reference and Guides (Wikipedia)",
            url=f"https://en.wikipedia.org/wiki/{query_encoded}",
            type="Documentation"
        ),
        Resource(
            title=f"{query} Beginner Video Course (YouTube)",
            url=f"https://www.youtube.com/results?search_query={query_encoded}+tutorial",
            type="Video"
        )
    ]
    
    # Filter resources to ensure they meet search quality rules
    filtered_resources = []
    for res in fallback_resources:
        if filter_url(res.url):
            filtered_resources.append(res)
            
    return filtered_resources
