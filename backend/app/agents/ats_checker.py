"""
ATS (Applicant Tracking System) Checker for AI Career Elevate.
Provides deterministic scoring and analysis of resume compatibility with ATS systems.
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ATSConfidence(Enum):
    """Confidence levels for ATS analysis."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ATSIssue:
    """Represents an ATS issue found in the resume."""
    category: str
    severity: str  # "critical", "major", "minor"
    message: str
    recommendation: str


@dataclass
class ATSBreakdown:
    """Detailed breakdown of ATS scoring by category."""
    file_text_extractable: float
    layout: float
    headers: float
    contact: float
    skills: float
    experience: float
    dates: float
    fonts_images: float
    length: float


@dataclass
class ATSReport:
    """Complete ATS analysis report."""
    score: float  # Overall score (0-100)
    breakdown: ATSBreakdown
    issues: List[ATSIssue]
    recommended_actions: List[str]
    confidence: ATSConfidence


class ATSChecker:
    """ATS compatibility checker with deterministic rules."""
    
    # Scoring weights for different categories
    WEIGHTS = {
        "file_text_extractable": 0.15,  # 15%
        "layout": 0.15,                 # 15%
        "headers": 0.12,                # 12%
        "contact": 0.10,                # 10%
        "skills": 0.15,                 # 15%
        "experience": 0.15,             # 15%
        "dates": 0.08,                  # 8%
        "fonts_images": 0.05,           # 5%
        "length": 0.05                  # 5%
    }
    
    # Optimal resume length range (words)
    OPTIMAL_LENGTH_MIN = 400
    OPTIMAL_LENGTH_MAX = 800
    
    # Common ATS-friendly headers
    ATS_HEADERS = {
        "contact", "personal information", "contact information",
        "summary", "professional summary", "objective", "profile",
        "experience", "work experience", "employment", "professional experience",
        "education", "academic background", "qualifications",
        "skills", "technical skills", "core competencies", "expertise",
        "certifications", "certificates", "licenses",
        "projects", "portfolio", "achievements", "accomplishments"
    }
    
    # Common professional skills keywords
    SKILL_KEYWORDS = {
        # Technical skills
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "express", "django", "flask", "spring", "laravel",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
        "git", "github", "gitlab", "ci/cd", "devops", "agile", "scrum",
        
        # Soft skills
        "leadership", "teamwork", "communication", "problem solving",
        "project management", "time management", "analytical", "creative",
        "collaboration", "mentoring", "training", "presentation"
    }
    
    def __init__(self):
        """Initialize the ATS checker."""
        self.issues: List[ATSIssue] = []
        self.recommended_actions: List[str] = []
    
    def run_ats_checks(self, resume_json: Dict[str, Any], raw_text: str) -> ATSReport:
        """
        Run comprehensive ATS checks on resume data.
        
        Args:
            resume_json: Parsed resume data in JSON format
            raw_text: Raw text extracted from resume file
            
        Returns:
            ATSReport with complete analysis
        """
        # Handle None inputs
        if resume_json is None:
            resume_json = {}
        if raw_text is None:
            raw_text = ""
        
        # Reset state
        self.issues = []
        self.recommended_actions = []
        
        # Calculate scores for each category
        breakdown = ATSBreakdown(
            file_text_extractable=self._check_file_text_extractable(raw_text),
            layout=self._check_layout(resume_json, raw_text),
            headers=self._check_headers(resume_json, raw_text),
            contact=self._check_contact(resume_json, raw_text),
            skills=self._check_skills(resume_json, raw_text),
            experience=self._check_experience(resume_json, raw_text),
            dates=self._check_dates(resume_json, raw_text),
            fonts_images=self._check_fonts_images(resume_json, raw_text),
            length=self._check_length(raw_text)
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(breakdown)
        
        # Determine confidence level
        confidence = self._determine_confidence(breakdown, len(raw_text))
        
        return ATSReport(
            score=overall_score,
            breakdown=breakdown,
            issues=self.issues,
            recommended_actions=self.recommended_actions,
            confidence=confidence
        )
    
    def _check_file_text_extractable(self, raw_text: str) -> float:
        """Check if file text is extractable and readable."""
        if not raw_text or len(raw_text.strip()) < 50:
            self.issues.append(ATSIssue(
                category="file_text_extractable",
                severity="critical",
                message="Resume text is too short or unreadable",
                recommendation="Ensure the resume file is properly formatted and contains sufficient content"
            ))
            return 0.0
        
        # Check for encoding issues or garbled text
        garbled_indicators = ["", "cid:", "\x00", "\ufffd"]
        garbled_count = sum(raw_text.count(indicator) for indicator in garbled_indicators)
        
        if garbled_count > len(raw_text) * 0.05:  # More than 5% garbled
            self.issues.append(ATSIssue(
                category="file_text_extractable",
                severity="major",
                message=f"Text contains {garbled_count} encoding issues",
                recommendation="Re-save the resume in a standard format (PDF or DOCX)"
            ))
            return 30.0
        
        # Check for meaningful content
        word_count = len(raw_text.split())
        if word_count < 100:
            self.issues.append(ATSIssue(
                category="file_text_extractable",
                severity="major",
                message=f"Resume has only {word_count} words",
                recommendation="Add more detailed content to your resume"
            ))
            return 60.0
        
        return 100.0
    
    def _check_layout(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check resume layout and structure."""
        score = 100.0
        
        # Check for tables (problematic for ATS)
        table_indicators = ["|", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴"]
        table_count = sum(raw_text.count(indicator) for indicator in table_indicators)
        
        if table_count > 10:
            self.issues.append(ATSIssue(
                category="layout",
                severity="major",
                message="Resume contains complex table formatting",
                recommendation="Use simple bullet points and standard formatting instead of tables"
            ))
            score -= 30.0
        
        # Check for columns (problematic for ATS)
        if "  " in raw_text and raw_text.count("\n") < len(raw_text.split()) * 0.1:
            self.issues.append(ATSIssue(
                category="layout",
                severity="minor",
                message="Resume may use column formatting",
                recommendation="Use single-column layout for better ATS compatibility"
            ))
            score -= 10.0
        
        # Check for proper line breaks
        lines = raw_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 10:
            self.issues.append(ATSIssue(
                category="layout",
                severity="major",
                message="Resume has insufficient structure",
                recommendation="Add proper sections and line breaks"
            ))
            score -= 20.0
        
        return max(0.0, score)
    
    def _check_headers(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for proper section headers."""
        score = 0.0
        found_headers = []
        
        # Look for common headers in the text
        text_lower = raw_text.lower()
        for header in self.ATS_HEADERS:
            if header in text_lower:
                found_headers.append(header)
        
        # Check JSON structure for headers
        if resume_json:
            json_headers = []
            for key in resume_json.keys():
                if isinstance(key, str) and key.lower() in self.ATS_HEADERS:
                    json_headers.append(key.lower())
            found_headers.extend(json_headers)
        
        # Score based on number of found headers
        unique_headers = set(found_headers)
        if len(unique_headers) >= 5:
            score = 100.0
        elif len(unique_headers) >= 3:
            score = 80.0
        elif len(unique_headers) >= 2:
            score = 60.0
        elif len(unique_headers) >= 1:
            score = 40.0
        
        if len(unique_headers) < 3:
            missing_headers = ["experience", "skills", "education"]
            self.issues.append(ATSIssue(
                category="headers",
                severity="major",
                message=f"Missing important section headers. Found: {list(unique_headers)}",
                recommendation=f"Add clear section headers like: {', '.join(missing_headers)}"
            ))
        
        return score
    
    def _check_contact(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for contact information."""
        score = 0.0
        contact_found = []
        
        # Check for email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, raw_text)
        if emails:
            contact_found.append("email")
            score += 30.0
        
        # Check for phone number
        phone_pattern = r'(\+?1[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        phones = re.findall(phone_pattern, raw_text)
        if phones:
            contact_found.append("phone")
            score += 30.0
        
        # Check for location (look for common city/state patterns)
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, State
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # City Name
            r'\b(address|location):\s*[^\n]+\b'  # Address: or Location:
        ]
        
        for pattern in location_patterns:
            if re.search(pattern, raw_text, re.IGNORECASE):
                contact_found.append("location")
                score += 20.0
                break
        
        # Check JSON structure
        if resume_json:
            contact_keys = ["email", "phone", "address", "location", "contact"]
            for key in contact_keys:
                if key.lower() in resume_json:
                    if key.lower() not in contact_found:
                        contact_found.append(key.lower())
                        score += 20.0
                elif key in resume_json:  # Check exact key match
                    if key.lower() not in contact_found:
                        contact_found.append(key.lower())
                        score += 20.0
        
        if not contact_found:
            self.issues.append(ATSIssue(
                category="contact",
                severity="critical",
                message="No contact information found",
                recommendation="Add email, phone number, and location to your resume"
            ))
        elif len(contact_found) < 2:
            self.issues.append(ATSIssue(
                category="contact",
                severity="major",
                message=f"Limited contact information. Found: {contact_found}",
                recommendation="Add missing contact details (email, phone, location)"
            ))
        
        return min(100.0, score)
    
    def _check_skills(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for skills section and relevant keywords."""
        score = 0.0
        skills_found = []
        
        # Look for skills in text
        text_lower = raw_text.lower()
        for skill in self.SKILL_KEYWORDS:
            if skill in text_lower:
                skills_found.append(skill)
        
        # Check JSON structure for skills
        if resume_json:
            if "skills" in resume_json:
                json_skills = resume_json["skills"]
                if isinstance(json_skills, list):
                    skills_found.extend([skill.lower() for skill in json_skills if isinstance(skill, str)])
                elif isinstance(json_skills, str):
                    skills_found.extend(json_skills.lower().split())
        
        # Score based on number of relevant skills found
        unique_skills = set(skills_found)
        if len(unique_skills) >= 10:
            score = 100.0
        elif len(unique_skills) >= 7:
            score = 80.0
        elif len(unique_skills) >= 5:
            score = 60.0
        elif len(unique_skills) >= 3:
            score = 40.0
        elif len(unique_skills) >= 1:
            score = 20.0
        
        if len(unique_skills) < 5:
            self.issues.append(ATSIssue(
                category="skills",
                severity="major",
                message=f"Limited skills identified. Found: {len(unique_skills)} relevant skills",
                recommendation="Add more specific technical and soft skills to your resume"
            ))
        
        return score
    
    def _check_experience(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for work experience section."""
        score = 0.0
        
        # Look for experience-related keywords
        experience_keywords = ["experience", "work", "employment", "job", "position", "role"]
        text_lower = raw_text.lower()
        experience_found = any(keyword in text_lower for keyword in experience_keywords)
        
        if experience_found:
            score += 30.0
        
        # Check for job titles and companies
        # Look for patterns like "Software Engineer at Company"
        job_patterns = [
            r'\b(at|@)\s+[A-Z][a-zA-Z\s&]+',  # "at Company"
            r'\b(software|engineer|developer|manager|analyst|specialist|coordinator|director|lead|senior|junior)\b',
        ]
        
        pattern_matches = 0
        for pattern in job_patterns:
            matches = re.findall(pattern, text_lower)
            pattern_matches += len(matches)
        
        if pattern_matches >= 5:
            score += 40.0
        elif pattern_matches >= 3:
            score += 30.0
        elif pattern_matches >= 1:
            score += 20.0
        
        # Check JSON structure
        if resume_json:
            exp_keys = ["experience", "work_experience", "employment", "jobs"]
            for key in exp_keys:
                if key.lower() in resume_json:
                    exp_data = resume_json[key.lower()]
                    if isinstance(exp_data, list) and len(exp_data) > 0:
                        score += 30.0
                        break
                elif key in resume_json:  # Check exact key match
                    exp_data = resume_json[key]
                    if isinstance(exp_data, list) and len(exp_data) > 0:
                        score += 30.0
                        break
        
        if score < 50:
            self.issues.append(ATSIssue(
                category="experience",
                severity="major",
                message="Work experience section is unclear or missing",
                recommendation="Add a clear work experience section with job titles, companies, and dates"
            ))
        
        return min(100.0, score)
    
    def _check_dates(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for proper date formatting."""
        score = 0.0
        
        # Look for various date formats
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years (1900-2099)
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',  # Month Year
            r'\b\d{1,2}[/-]\d{4}\b',  # MM/YYYY or MM-YYYY
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        
        total_dates = 0
        for pattern in date_patterns:
            dates = re.findall(pattern, raw_text, re.IGNORECASE)
            total_dates += len(dates)
        
        if total_dates >= 6:
            score = 100.0
        elif total_dates >= 4:
            score = 80.0
        elif total_dates >= 2:
            score = 60.0
        elif total_dates >= 1:
            score = 40.0
        
        if total_dates < 2:
            self.issues.append(ATSIssue(
                category="dates",
                severity="major",
                message=f"Limited date information found ({total_dates} dates)",
                recommendation="Add dates for education, work experience, and certifications"
            ))
        
        return score
    
    def _check_fonts_images(self, resume_json: Dict[str, Any], raw_text: str) -> float:
        """Check for ATS-friendly fonts and absence of images."""
        score = 100.0
        
        # Check for image references (problematic for ATS)
        image_indicators = ["image", "img", "photo", "picture", "logo", "graphic"]
        text_lower = raw_text.lower()
        
        image_count = sum(text_lower.count(indicator) for indicator in image_indicators)
        if image_count > 0:
            self.issues.append(ATSIssue(
                category="fonts_images",
                severity="minor",
                message=f"Found {image_count} potential image references",
                recommendation="Avoid images, logos, or graphics in your resume for better ATS compatibility"
            ))
            score -= 20.0
        
        # Check for special characters that might indicate formatting issues
        special_chars = ["©", "®", "™", "◦", "▪", "▫", "◆", "◇", "★", "☆"]
        special_char_count = sum(raw_text.count(char) for char in special_chars)
        
        if special_char_count > 5:
            self.issues.append(ATSIssue(
                category="fonts_images",
                severity="minor",
                message=f"Found {special_char_count} special characters",
                recommendation="Use standard bullet points and characters for better ATS compatibility"
            ))
            score -= 10.0
        
        return max(0.0, score)
    
    def _check_length(self, raw_text: str) -> float:
        """Check resume length."""
        word_count = len(raw_text.split())
        
        if self.OPTIMAL_LENGTH_MIN <= word_count <= self.OPTIMAL_LENGTH_MAX:
            return 100.0
        elif word_count < self.OPTIMAL_LENGTH_MIN:
            self.issues.append(ATSIssue(
                category="length",
                severity="major",
                message=f"Resume is too short ({word_count} words)",
                recommendation=f"Aim for {self.OPTIMAL_LENGTH_MIN}-{self.OPTIMAL_LENGTH_MAX} words for optimal length"
            ))
            return 60.0
        else:
            self.issues.append(ATSIssue(
                category="length",
                severity="minor",
                message=f"Resume is long ({word_count} words)",
                recommendation=f"Consider condensing to {self.OPTIMAL_LENGTH_MAX} words or less"
            ))
            return 80.0
    
    def _calculate_overall_score(self, breakdown: ATSBreakdown) -> float:
        """Calculate weighted overall ATS score."""
        total_score = 0.0
        
        total_score += breakdown.file_text_extractable * self.WEIGHTS["file_text_extractable"]
        total_score += breakdown.layout * self.WEIGHTS["layout"]
        total_score += breakdown.headers * self.WEIGHTS["headers"]
        total_score += breakdown.contact * self.WEIGHTS["contact"]
        total_score += breakdown.skills * self.WEIGHTS["skills"]
        total_score += breakdown.experience * self.WEIGHTS["experience"]
        total_score += breakdown.dates * self.WEIGHTS["dates"]
        total_score += breakdown.fonts_images * self.WEIGHTS["fonts_images"]
        total_score += breakdown.length * self.WEIGHTS["length"]
        
        return round(total_score, 1)
    
    def _determine_confidence(self, breakdown: ATSBreakdown, text_length: int) -> ATSConfidence:
        """Determine confidence level based on analysis completeness."""
        # Check if we have enough data for reliable analysis
        if text_length < 200:
            return ATSConfidence.LOW
        elif text_length < 500:
            return ATSConfidence.MEDIUM
        else:
            return ATSConfidence.HIGH


def run_ats_checks(resume_json: Dict[str, Any], raw_text: str) -> ATSReport:
    """
    Main function to run ATS checks on resume data.
    
    Args:
        resume_json: Parsed resume data in JSON format
        raw_text: Raw text extracted from resume file
        
    Returns:
        ATSReport with complete analysis
    """
    checker = ATSChecker()
    return checker.run_ats_checks(resume_json, raw_text)
