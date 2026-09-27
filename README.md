# CV Shield

CV Shield is a Python-based document analysis tool designed to detect suspicious instructions and potential prompt injection attempts in PDF resumes.

The project explores how malicious or manipulative instructions embedded in resumes could affect AI-powered recruitment systems.

## The Problem

AI-powered recruitment systems are increasingly used to analyze and screen resumes.

This creates a potential security concern: a PDF resume may contain instructions designed to manipulate an AI system into changing how the document or candidate is evaluated.

CV Shield was created to investigate this type of risk by analyzing resume content and identifying suspicious patterns that may require human review.

## What CV Shield Does

The current version extracts text from PDF resumes and checks it for predefined suspicious patterns, including:

- Attempts to override previous instructions
- Instructions designed to influence hiring recommendations
- Attempts to automatically approve a resume
- Attempts to bypass manual review

The project is also being developed toward detecting hidden or invisible PDF content, including:

- White-on-white text
- Zero-size text
- Off-page content
- Other potentially hidden content based on PDF structure and formatting

**Important:** CV Shield does not make hiring decisions. It only identifies potential evidence for human review.

## Current MVP

The current MVP focuses on:

1. Extracting text from PDF resumes using Python and `pypdf`
2. Detecting predefined suspicious text patterns
3. Categorizing detected patterns
4. Generating structured scan reports
5. Producing JSON output
6. Running automated tests against fictional resumes with different suspicious instruction patterns

## Test Cases

The project uses fictional resumes to validate the detection logic.

Current test cases include:

- Instruction override attempts
- Hiring recommendation manipulation
- Attempts to automatically approve a candidate
- Attempts to bypass manual review
- Attempts to manipulate technical evaluation results

The test resumes are intentionally fictional and contain different suspicious instruction patterns to help validate and expand the detector.

## Tech Stack

- Python
- pypdf
- unittest
- Git & GitHub
- n8n (planned)

## Development Roadmap

- [x] **Step 1 — Project definition and initial setup**
- [x] **Step 2 — Environment setup and basic PDF text extraction**
- [x] **Step 3 — Initial suspicious-pattern detector**
- [x] **Step 4 — Structured scan report generation**
- [x] **Step 5 — JSON output and automated testing**
- [ ] **Step 6 — Hidden-text detection and PDF structure analysis**
- [ ] **Step 7 — AI-assisted analysis of suspicious instructions**
- [ ] **Step 8 — n8n integration and workflow automation**
- [ ] **Step 9 — Expanded testing and validation**

## Status

🚧 **Work in progress**

CV Shield is being developed incrementally, with new detection rules, tests, experiments, and improvements added throughout the project.

## Ethical Considerations

All test resumes used in this project are fictional.

CV Shield is designed to support human review, not to make hiring decisions or determine whether a candidate should be hired or rejected.