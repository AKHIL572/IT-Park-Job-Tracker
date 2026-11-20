import re
from typing import List, Dict, Any, Tuple
from database import get_all_skills

def match_skills_for_title(title: str, skills_list: List[Dict[str, Any]] = None) -> Tuple[str, List[str]]:
    """
    Evaluates skill match for a given job title.
    Returns (level: 'High' | 'Possible' | 'Low', matched_skills: List[str])
    """
    if not title:
        return ("Low", [])
    
    if skills_list is None:
        skills_list = get_all_skills()

    matched_skills = []
    has_high_priority = False

    title_lower = title.lower()

    for s in skills_list:
        skill_name = s["name"]
        escaped_skill = re.escape(skill_name.lower())
        
        # Word boundary matching so 'Java' does not match 'JavaScript' unless both are present
        # Handle special characters like .NET, C#, C++
        if re.search(r'[#\+\.]', skill_name):
            pattern = rf'(?:^|[\s,/\-\(\)\[\]]){escaped_skill}(?:$|[\s,/\-\(\)\[\]])'
        else:
            pattern = rf'\b{escaped_skill}\b'

        if re.search(pattern, title_lower):
            matched_skills.append(skill_name)
            if s.get("is_core", 0) == 1 or s.get("priority", 1) >= 2:
                has_high_priority = True

    count = len(matched_skills)
    if count >= 2 or has_high_priority:
        level = "High"
    elif count == 1:
        level = "Possible"
    else:
        level = "Low"

    return (level, matched_skills)

def annotate_jobs_with_skills(jobs: List[Dict[str, Any]], skills_list: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Annotates each job dictionary with 'skill_match' and 'matched_skills'."""
    if skills_list is None:
        skills_list = get_all_skills()

    annotated = []
    for j in jobs:
        d = dict(j)
        level, matched = match_skills_for_title(d.get("title", ""), skills_list)
        d["skill_match"] = level
        d["matched_skills"] = matched
        annotated.append(d)
    return annotated

