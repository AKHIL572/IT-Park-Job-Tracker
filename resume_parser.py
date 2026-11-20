import re
import os
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Set

# Known technology skill dictionary with auto-categorization
TECH_SKILLS_CATALOG = {
    # Programming Languages
    "Python": "Programming Language",
    "JavaScript": "Programming Language",
    "TypeScript": "Programming Language",
    "Java": "Programming Language",
    "C": "Programming Language",
    "C++": "Programming Language",
    "C#": "Programming Language",
    "Golang": "Programming Language",
    "Go": "Programming Language",
    "Rust": "Programming Language",
    "PHP": "Programming Language",
    "Ruby": "Programming Language",
    "Kotlin": "Programming Language",
    "Swift": "Programming Language",
    "Scala": "Programming Language",
    "R": "Programming Language",
    "Dart": "Programming Language",
    "Perl": "Programming Language",
    "Shell": "Programming Language",
    "Bash": "Programming Language",

    # Databases
    "SQL": "Database",
    "MySQL": "Database",
    "PostgreSQL": "Database",
    "Postgres": "Database",
    "MongoDB": "Database",
    "Redis": "Database",
    "SQLite": "Database",
    "Oracle": "Database",
    "SQL Server": "Database",
    "MSSQL": "Database",
    "Cassandra": "Database",
    "DynamoDB": "Database",
    "MariaDB": "Database",
    "Firebase": "Database",
    "Supabase": "Database",
    "Elasticsearch": "Database",
    "Neo4j": "Database",

    # Frameworks & Backend
    "React": "Framework & Web",
    "React Native": "Framework & Web",
    "Angular": "Framework & Web",
    "Vue": "Framework & Web",
    "Vue.js": "Framework & Web",
    "Next.js": "Framework & Web",
    "Nuxt": "Framework & Web",
    "Node": "Framework & Web",
    "Node.js": "Framework & Web",
    "Express": "Framework & Web",
    "NestJS": "Framework & Web",
    "Django": "Framework & Web",
    "Flask": "Framework & Web",
    "FastAPI": "Framework & Web",
    "Spring": "Framework & Web",
    "Spring Boot": "Framework & Web",
    "Laravel": "Framework & Web",
    ".NET": "Framework & Web",
    ".NET Core": "Framework & Web",
    "ASP.NET": "Framework & Web",
    "Ruby on Rails": "Framework & Web",
    "Flutter": "Framework & Web",
    "Svelte": "Framework & Web",
    "GraphQL": "Framework & Web",
    "REST API": "Framework & Web",
    "Microservices": "Framework & Web",

    # Frontend
    "HTML": "Frontend",
    "HTML5": "Frontend",
    "CSS": "Frontend",
    "CSS3": "Frontend",
    "Tailwind": "Frontend",
    "Tailwind CSS": "Frontend",
    "Bootstrap": "Frontend",
    "SASS": "Frontend",
    "SCSS": "Frontend",
    "Redux": "Frontend",
    "Webpack": "Frontend",
    "Vite": "Frontend",
    "jQuery": "Frontend",

    # DevOps & Cloud
    "Docker": "DevOps & Cloud",
    "Kubernetes": "DevOps & Cloud",
    "AWS": "DevOps & Cloud",
    "Amazon Web Services": "DevOps & Cloud",
    "Azure": "DevOps & Cloud",
    "GCP": "DevOps & Cloud",
    "Google Cloud": "DevOps & Cloud",
    "Linux": "DevOps & Cloud",
    "Git": "DevOps & Cloud",
    "GitHub": "DevOps & Cloud",
    "GitLab": "DevOps & Cloud",
    "CI/CD": "DevOps & Cloud",
    "Jenkins": "DevOps & Cloud",
    "Terraform": "DevOps & Cloud",
    "Ansible": "DevOps & Cloud",
    "Nginx": "DevOps & Cloud",
    "Apache": "DevOps & Cloud",

    # Testing & QA
    "QA": "Testing & QA",
    "Manual Testing": "Testing & QA",
    "Automation Testing": "Testing & QA",
    "Selenium": "Testing & QA",
    "Cypress": "Testing & QA",
    "Playwright": "Testing & QA",
    "JUnit": "Testing & QA",
    "PyTest": "Testing & QA",
    "Jest": "Testing & QA",
    "Postman": "Testing & QA",
    "JMeter": "Testing & QA",

    # AI & Data Science
    "Machine Learning": "AI & Data",
    "Deep Learning": "AI & Data",
    "Data Science": "AI & Data",
    "Artificial Intelligence": "AI & Data",
    "NLP": "AI & Data",
    "Computer Vision": "AI & Data",
    "Pandas": "AI & Data",
    "NumPy": "AI & Data",
    "Scikit-learn": "AI & Data",
    "TensorFlow": "AI & Data",
    "PyTorch": "AI & Data",
    "Keras": "AI & Data",
    "Tableau": "AI & Data",
    "Power BI": "AI & Data",

    # Design
    "UI/UX": "Design & UI/UX",
    "Figma": "Design & UI/UX",
    "Adobe XD": "Design & UI/UX",
    "Photoshop": "Design & UI/UX",
    "Illustrator": "Design & UI/UX",
    "Graphic Design": "Design & UI/UX",
    "Wireframing": "Design & UI/UX",

    # Roles & Core
    "Full Stack": "Role",
    "Frontend Developer": "Role",
    "Backend Developer": "Role",
    "DevOps Engineer": "Role",
    "Data Engineer": "Role",
    "Product Manager": "Role",
    "Scrum Master": "Role",
    "Agile": "Role",
    "Jira": "Tools",
}

def auto_categorize_skill(skill_name: str) -> str:
    """Automatically assigns a category to any skill name."""
    clean = skill_name.strip()
    # Check exact catalog match (case-insensitive)
    for k, v in TECH_SKILLS_CATALOG.items():
        if k.lower() == clean.lower():
            return v

    lower = clean.lower()
    # Heuristic rules for unknown skills
    if any(w in lower for w in ['sql', 'db', 'data', 'store', 'mongo', 'postgres', 'redis']):
        return "Database"
    elif any(w in lower for w in ['script', 'lang', 'python', 'java', 'c++', 'c#', 'ruby', 'rust', 'go']):
        return "Programming Language"
    elif any(w in lower for w in ['react', 'vue', 'angular', 'spring', 'django', 'flask', 'api', 'framework']):
        return "Framework & Web"
    elif any(w in lower for w in ['cloud', 'aws', 'azure', 'docker', 'kube', 'devops', 'linux', 'deploy', 'ci/cd']):
        return "DevOps & Cloud"
    elif any(w in lower for w in ['test', 'qa', 'selenium', 'cypress', 'automation', 'quality']):
        return "Testing & QA"
    elif any(w in lower for w in ['design', 'ui', 'ux', 'figma', 'xd', 'graphic', 'css', 'style']):
        return "Design & UI/UX"
    elif any(w in lower for w in ['ai', 'ml', 'learn', 'neural', 'vision', 'model', 'nlp']):
        return "AI & Data"
    elif any(w in lower for w in ['engineer', 'developer', 'manager', 'lead', 'architect', 'analyst']):
        return "Role"
    else:
        return "Tools & Technologies"

def extract_text_from_pdf(file_stream: io.BytesIO) -> str:
    """Extract text from PDF using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(file_stream)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception as e:
        print("PDF extraction error:", e)
        return ""

def extract_text_from_docx(file_stream: io.BytesIO) -> str:
    """Extract text from DOCX using standard zipfile & XML."""
    try:
        with zipfile.ZipFile(file_stream) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Find all text elements <w:t>
            text_nodes = tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
            return " ".join([t.text for t in text_nodes if t.text])
    except Exception as e:
        print("DOCX extraction error:", e)
        return ""

def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract text from PDF, DOCX, or TXT."""
    ext = os.path.splitext(filename)[1].lower()
    bio = io.BytesIO(file_bytes)

    if ext == ".pdf":
        return extract_text_from_pdf(bio)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(bio)
    elif ext in (".txt", ".md", ".rtf"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore")
    else:
        # Fallback decode
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""

def extract_skills_from_text(text: str, existing_skills: List[str] = None) -> List[Dict[str, Any]]:
    """
    Finds skills from text matching TECH_SKILLS_CATALOG,
    excluding existing skills.
    """
    if not text:
        return []

    existing_set = {s.lower() for s in (existing_skills or [])}
    found_skills = []
    seen = set()

    # Pre-clean text
    text_lower = f" {text.lower()} "

    for skill_name, category in TECH_SKILLS_CATALOG.items():
        low_name = skill_name.lower()
        if low_name in existing_set or low_name in seen:
            continue

        # Regex word boundary check
        if re.search(r'[#\+\.]', skill_name):
            pattern = rf'(?:^|[\s,/\-\(\)\[\]]){re.escape(low_name)}(?:$|[\s,/\-\(\)\[\]])'
        else:
            pattern = rf'\b{re.escape(low_name)}\b'

        if re.search(pattern, text_lower):
            seen.add(low_name)
            # Determine if commonly core
            is_core = category in ("Programming Language", "Framework & Web", "Database")
            found_skills.append({
                "name": skill_name,
                "category": category,
                "is_core": is_core
            })

    # Sort: Core skills first, then alphabetically
    found_skills.sort(key=lambda s: (not s["is_core"], s["name"]))
    return found_skills

