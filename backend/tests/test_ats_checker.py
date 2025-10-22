"""
Comprehensive tests for the ATS checker system.
Tests deterministic scoring rules with various resume scenarios.
"""
import pytest
from app.agents.ats_checker import (
    ATSChecker, 
    run_ats_checks, 
    ATSReport, 
    ATSBreakdown, 
    ATSIssue, 
    ATSConfidence
)


class TestATSCheckerBasic:
    """Test basic ATS checker functionality."""
    
    def test_ats_checker_initialization(self):
        """Test ATS checker initialization."""
        checker = ATSChecker()
        assert checker.issues == []
        assert checker.recommended_actions == []
    
    def test_run_ats_checks_function(self):
        """Test the main run_ats_checks function."""
        resume_json = {"skills": ["Python", "JavaScript"]}
        raw_text = "John Doe\nSoftware Engineer\nEmail: john@example.com"
        
        report = run_ats_checks(resume_json, raw_text)
        
        assert isinstance(report, ATSReport)
        assert 0 <= report.score <= 100
        assert isinstance(report.breakdown, ATSBreakdown)
        assert isinstance(report.issues, list)
        assert isinstance(report.recommended_actions, list)
        assert isinstance(report.confidence, ATSConfidence)


class TestATSCheckerScoring:
    """Test ATS scoring functionality."""
    
    def test_perfect_resume_scoring(self):
        """Test scoring for a perfect ATS-friendly resume."""
        perfect_resume_json = {
            "contact": {
                "email": "john.doe@example.com",
                "phone": "(555) 123-4567",
                "location": "San Francisco, CA"
            },
            "summary": "Experienced software engineer with 5+ years in Python development",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "dates": "2020-2024",
                    "description": "Led development of web applications using Python and React"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Computer Science",
                    "school": "University of Technology",
                    "dates": "2016-2020"
                }
            ],
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker",
                "Leadership", "Teamwork", "Problem Solving", "Communication"
            ]
        }
        
        perfect_raw_text = """
        John Doe
        Senior Software Engineer
        Email: john.doe@example.com
        Phone: (555) 123-4567
        Location: San Francisco, CA
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 5+ years in Python development and web technologies.
        
        EXPERIENCE
        Senior Software Engineer | Tech Corp | 2020-2024
        • Led development of web applications using Python and React
        • Managed team of 5 developers
        • Implemented CI/CD pipelines with Docker and AWS
        
        Software Engineer | Startup Inc | 2018-2020
        • Developed RESTful APIs using Python and Django
        • Built responsive frontend applications with React
        • Collaborated with product team on feature requirements
        
        EDUCATION
        Bachelor of Computer Science | University of Technology | 2016-2020
        • GPA: 3.8/4.0
        • Relevant Coursework: Data Structures, Algorithms, Database Systems
        
        SKILLS
        Technical: Python, JavaScript, React, Node.js, SQL, AWS, Docker, Git
        Soft: Leadership, Teamwork, Problem Solving, Communication, Project Management
        
        CERTIFICATIONS
        AWS Certified Developer | 2023
        Google Cloud Professional Developer | 2022
        """
        
        report = run_ats_checks(perfect_resume_json, perfect_raw_text)
        
        # Should have high score
        assert report.score >= 80
        assert report.confidence == ATSConfidence.HIGH
        
        # Check breakdown scores
        assert report.breakdown.file_text_extractable >= 90
        assert report.breakdown.layout >= 80
        assert report.breakdown.headers >= 80
        assert report.breakdown.contact >= 90
        assert report.breakdown.skills >= 80
        assert report.breakdown.experience >= 80
        assert report.breakdown.dates >= 80
    
    def test_poor_resume_scoring(self):
        """Test scoring for a poor ATS resume."""
        poor_resume_json = {}
        poor_raw_text = "John Doe Software Engineer"
        
        report = run_ats_checks(poor_resume_json, poor_raw_text)
        
        # Should have low score
        assert report.score < 50
        assert report.confidence == ATSConfidence.LOW
        
        # Should have many issues
        assert len(report.issues) > 5
        
        # Check for critical issues
        critical_issues = [issue for issue in report.issues if issue.severity == "critical"]
        assert len(critical_issues) > 0
    
    def test_medium_resume_scoring(self):
        """Test scoring for a medium-quality resume."""
        medium_resume_json = {
            "contact": {"email": "john@example.com"},
            "experience": [{"title": "Developer", "company": "Company"}],
            "skills": ["Python", "JavaScript"]
        }
        
        medium_raw_text = """
        John Doe
        Software Developer
        Email: john@example.com
        
        EXPERIENCE
        Software Developer at Tech Company
        • Worked on web applications
        • Used Python and JavaScript
        
        SKILLS
        Python, JavaScript, HTML, CSS
        
        EDUCATION
        Computer Science Degree from University
        """
        
        report = run_ats_checks(medium_resume_json, medium_raw_text)
        
        # Should have medium score
        assert 40 <= report.score <= 70
        assert report.confidence in [ATSConfidence.MEDIUM, ATSConfidence.HIGH]
        
        # Should have some issues but not critical ones
        issues = report.issues
        assert len(issues) > 0
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        assert len(critical_issues) < 3


class TestFileTextExtractable:
    """Test file text extractable scoring."""
    
    def test_good_text_extractable(self):
        """Test good text extractable scenario."""
        checker = ATSChecker()
        good_text = "This is a well-formatted resume with plenty of content. " * 20
        
        score = checker._check_file_text_extractable(good_text)
        
        assert score == 100.0
        assert len(checker.issues) == 0
    
    def test_short_text_extractable(self):
        """Test short text scenario."""
        checker = ATSChecker()
        short_text = "John Doe"
        
        score = checker._check_file_text_extractable(short_text)
        
        assert score == 0.0
        assert len(checker.issues) == 1
        assert checker.issues[0].severity == "critical"
        assert "too short" in checker.issues[0].message
    
    def test_garbled_text_extractable(self):
        """Test garbled text scenario."""
        checker = ATSChecker()
        garbled_text = "John Doe" + "" * 10 + "Software Engineer" + "" * 5
        
        score = checker._check_file_text_extractable(garbled_text)
        
        assert score == 30.0
        assert len(checker.issues) == 1
        assert checker.issues[0].severity == "major"
        assert "encoding issues" in checker.issues[0].message


class TestLayoutScoring:
    """Test layout scoring functionality."""
    
    def test_good_layout(self):
        """Test good layout scenario."""
        checker = ATSChecker()
        good_text = """
        John Doe
        
        EXPERIENCE
        Software Engineer at Company A
        • Developed applications
        • Led team projects
        
        SKILLS
        Python, JavaScript, React
        """
        
        score = checker._check_layout({}, good_text)
        
        assert score >= 80
    
    def test_table_layout_issues(self):
        """Test table formatting issues."""
        checker = ATSChecker()
        table_text = """
        | Name    | Position        | Company |
        |---------|-----------------|---------|
        | John    | Engineer        | Tech    |
        ┌─────────┬─────────────────┬─────────┐
        │ Skill   │ Level           │ Years   │
        └─────────┴─────────────────┴─────────┘
        """
        
        score = checker._check_layout({}, table_text)
        
        assert score < 70
        table_issues = [issue for issue in checker.issues if issue.category == "layout"]
        assert len(table_issues) > 0
    
    def test_poor_structure_layout(self):
        """Test poor structure layout."""
        checker = ATSChecker()
        poor_text = "John Doe Software Engineer Python JavaScript React"
        
        score = checker._check_layout({}, poor_text)
        
        assert score < 80
        structure_issues = [issue for issue in checker.issues if "structure" in issue.message.lower()]
        assert len(structure_issues) > 0


class TestHeadersScoring:
    """Test headers scoring functionality."""
    
    def test_good_headers(self):
        """Test good headers scenario."""
        checker = ATSChecker()
        good_text = """
        CONTACT INFORMATION
        Email: john@example.com
        
        PROFESSIONAL SUMMARY
        Experienced developer
        
        EXPERIENCE
        Software Engineer
        
        EDUCATION
        Computer Science Degree
        
        SKILLS
        Python, JavaScript
        """
        
        score = checker._check_headers({}, good_text)
        
        assert score >= 80
    
    def test_json_headers(self):
        """Test headers from JSON structure."""
        checker = ATSChecker()
        resume_json = {
            "contact": "john@example.com",
            "summary": "Experienced developer",
            "experience": "Software Engineer",
            "education": "Computer Science Degree",
            "skills": ["Python", "JavaScript"]
        }
        
        score = checker._check_headers(resume_json, "")
        
        assert score >= 80
    
    def test_missing_headers(self):
        """Test missing headers scenario."""
        checker = ATSChecker()
        poor_text = "John Doe Software Engineer Python JavaScript"
        
        score = checker._check_headers({}, poor_text)
        
        assert score < 40
        header_issues = [issue for issue in checker.issues if issue.category == "headers"]
        assert len(header_issues) > 0


class TestContactScoring:
    """Test contact information scoring."""
    
    def test_complete_contact(self):
        """Test complete contact information."""
        checker = ATSChecker()
        complete_text = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        Location: San Francisco, CA
        """
        
        score = checker._check_contact({}, complete_text)
        
        assert score == 100.0
    
    def test_email_only_contact(self):
        """Test email only contact."""
        checker = ATSChecker()
        email_text = "John Doe\nEmail: john@example.com"
        
        score = checker._check_contact({}, email_text)
        
        assert score == 30.0
        contact_issues = [issue for issue in checker.issues if issue.category == "contact"]
        assert len(contact_issues) > 0
    
    def test_no_contact(self):
        """Test no contact information."""
        checker = ATSChecker()
        no_contact_text = "John Doe Software Engineer"
        
        score = checker._check_contact({}, no_contact_text)
        
        assert score == 0.0
        critical_issues = [issue for issue in checker.issues if issue.severity == "critical"]
        assert len(critical_issues) > 0
    
    def test_json_contact(self):
        """Test contact from JSON structure."""
        checker = ATSChecker()
        resume_json = {
            "email": "john@example.com",
            "phone": "(555) 123-4567",
            "address": "San Francisco, CA"
        }
        
        score = checker._check_contact(resume_json, "")
        
        assert score >= 80


class TestSkillsScoring:
    """Test skills scoring functionality."""
    
    def test_comprehensive_skills(self):
        """Test comprehensive skills scenario."""
        checker = ATSChecker()
        skills_text = """
        SKILLS
        Python, JavaScript, React, Node.js, SQL, AWS, Docker
        Leadership, Teamwork, Communication, Problem Solving
        """
        
        score = checker._check_skills({}, skills_text)
        
        assert score >= 80
    
    def test_json_skills(self):
        """Test skills from JSON structure."""
        checker = ATSChecker()
        resume_json = {
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "SQL", 
                "AWS", "Docker", "Leadership", "Teamwork"
            ]
        }
        
        score = checker._check_skills(resume_json, "")
        
        assert score >= 80
    
    def test_limited_skills(self):
        """Test limited skills scenario."""
        checker = ATSChecker()
        limited_text = "Python JavaScript"
        
        score = checker._check_skills({}, limited_text)
        
        assert score < 60
        skills_issues = [issue for issue in checker.issues if issue.category == "skills"]
        assert len(skills_issues) > 0


class TestExperienceScoring:
    """Test experience scoring functionality."""
    
    def test_good_experience(self):
        """Test good experience scenario."""
        checker = ATSChecker()
        experience_text = """
        EXPERIENCE
        Senior Software Engineer at Tech Corp (2020-2024)
        • Led development of web applications
        • Managed team of 5 developers
        
        Software Engineer at Startup Inc (2018-2020)
        • Developed RESTful APIs
        • Built responsive frontend applications
        """
        
        score = checker._check_experience({}, experience_text)
        
        assert score >= 70
    
    def test_json_experience(self):
        """Test experience from JSON structure."""
        checker = ATSChecker()
        resume_json = {
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "dates": "2020-2024",
                    "description": "Led development team"
                },
                {
                    "title": "Software Engineer", 
                    "company": "Startup Inc",
                    "dates": "2018-2020",
                    "description": "Developed applications"
                }
            ]
        }
        
        score = checker._check_experience(resume_json, "")
        
        assert score >= 70
    
    def test_poor_experience(self):
        """Test poor experience scenario."""
        checker = ATSChecker()
        poor_text = "John Doe Developer"
        
        score = checker._check_experience({}, poor_text)
        
        assert score < 50
        experience_issues = [issue for issue in checker.issues if issue.category == "experience"]
        assert len(experience_issues) > 0


class TestDatesScoring:
    """Test dates scoring functionality."""
    
    def test_comprehensive_dates(self):
        """Test comprehensive dates scenario."""
        checker = ATSChecker()
        dates_text = """
        EXPERIENCE
        Software Engineer at Company A (2020-2024)
        Developer at Company B (January 2018 - December 2019)
        
        EDUCATION
        Computer Science Degree (2016-2020)
        High School Diploma (2012-2016)
        
        CERTIFICATIONS
        AWS Certification (2023)
        Python Certification (2022)
        """
        
        score = checker._check_dates({}, dates_text)
        
        assert score >= 80
    
    def test_limited_dates(self):
        """Test limited dates scenario."""
        checker = ATSChecker()
        limited_text = "Experience from 2020 to 2024"
        
        score = checker._check_dates({}, limited_text)
        
        assert score <= 60
        dates_issues = [issue for issue in checker.issues if issue.category == "dates"]
        assert len(dates_issues) > 0
    
    def test_no_dates(self):
        """Test no dates scenario."""
        checker = ATSChecker()
        no_dates_text = "John Doe Software Engineer"
        
        score = checker._check_dates({}, no_dates_text)
        
        assert score == 0.0


class TestFontsImagesScoring:
    """Test fonts and images scoring."""
    
    def test_clean_formatting(self):
        """Test clean formatting scenario."""
        checker = ATSChecker()
        clean_text = """
        John Doe
        Software Engineer
        
        EXPERIENCE
        • Developed applications
        • Led team projects
        
        SKILLS
        Python, JavaScript, React
        """
        
        score = checker._check_fonts_images({}, clean_text)
        
        assert score == 100.0
    
    def test_image_references(self):
        """Test image references scenario."""
        checker = ATSChecker()
        image_text = """
        John Doe
        [Logo Image]
        Software Engineer
        
        Experience with image processing and photo editing
        """
        
        score = checker._check_fonts_images({}, image_text)
        
        assert score < 100.0
        image_issues = [issue for issue in checker.issues if issue.category == "fonts_images"]
        assert len(image_issues) > 0
    
    def test_special_characters(self):
        """Test special characters scenario."""
        checker = ATSChecker()
        special_text = """
        John Doe ©
        Software Engineer ®
        
        • Python Development ★
        • JavaScript Programming ☆
        • React Applications ◆
        """
        
        score = checker._check_fonts_images({}, special_text)
        
        assert score < 100.0


class TestLengthScoring:
    """Test resume length scoring."""
    
    def test_optimal_length(self):
        """Test optimal length scenario."""
        checker = ATSChecker()
        optimal_text = "John Doe Software Engineer " * 20  # ~500 words
        
        score = checker._check_length(optimal_text)
        
        assert score == 100.0
    
    def test_too_short(self):
        """Test too short scenario."""
        checker = ATSChecker()
        short_text = "John Doe Software Engineer"  # ~3 words
        
        score = checker._check_length(short_text)
        
        assert score == 60.0
        length_issues = [issue for issue in checker.issues if issue.category == "length"]
        assert len(length_issues) > 0
    
    def test_too_long(self):
        """Test too long scenario."""
        checker = ATSChecker()
        long_text = "John Doe Software Engineer " * 50  # ~1000 words
        
        score = checker._check_length(long_text)
        
        assert score <= 80.0
        length_issues = [issue for issue in checker.issues if issue.category == "length"]
        assert len(length_issues) > 0


class TestOverallScoring:
    """Test overall scoring calculations."""
    
    def test_weighted_scoring(self):
        """Test weighted scoring calculation."""
        checker = ATSChecker()
        
        # Create a breakdown with known scores
        breakdown = ATSBreakdown(
            file_text_extractable=100.0,
            layout=80.0,
            headers=90.0,
            contact=70.0,
            skills=85.0,
            experience=75.0,
            dates=60.0,
            fonts_images=100.0,
            length=80.0
        )
        
        overall_score = checker._calculate_overall_score(breakdown)
        
        # Calculate expected weighted score
        expected = (
            100.0 * 0.15 +  # file_text_extractable
            80.0 * 0.15 +   # layout
            90.0 * 0.12 +   # headers
            70.0 * 0.10 +   # contact
            85.0 * 0.15 +   # skills
            75.0 * 0.15 +   # experience
            60.0 * 0.08 +   # dates
            100.0 * 0.05 +  # fonts_images
            80.0 * 0.05     # length
        )
        
        assert abs(overall_score - expected) < 0.1
    
    def test_confidence_determination(self):
        """Test confidence level determination."""
        checker = ATSChecker()
        
        # Test high confidence
        breakdown = ATSBreakdown(80, 80, 80, 80, 80, 80, 80, 80, 80)
        confidence = checker._determine_confidence(breakdown, 600)
        assert confidence == ATSConfidence.HIGH
        
        # Test medium confidence
        confidence = checker._determine_confidence(breakdown, 300)
        assert confidence == ATSConfidence.MEDIUM
        
        # Test low confidence
        confidence = checker._determine_confidence(breakdown, 100)
        assert confidence == ATSConfidence.LOW


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_inputs(self):
        """Test empty inputs."""
        report = run_ats_checks({}, "")
        
        assert report.score >= 0.0  # Should handle gracefully
        assert report.confidence == ATSConfidence.LOW
        assert len(report.issues) > 0
    
    def test_none_inputs(self):
        """Test None inputs."""
        report = run_ats_checks(None, None)
        
        assert report.score >= 0.0  # Should handle gracefully
        assert report.confidence == ATSConfidence.LOW
    
    def test_very_long_text(self):
        """Test very long text input."""
        very_long_text = "John Doe Software Engineer " * 200  # ~4000 words
        report = run_ats_checks({}, very_long_text)
        
        assert report.score >= 0
        assert report.confidence == ATSConfidence.HIGH
    
    def test_unicode_text(self):
        """Test unicode text handling."""
        unicode_text = "José García\nSoftware Engineer\nExperiencia en Python y JavaScript"
        report = run_ats_checks({}, unicode_text)
        
        assert report.score >= 0
        assert isinstance(report.score, float)
