# CV Shield

CV Shield is a document analysis tool designed to detect suspicious instructions and potential prompt injection attempts in PDF resumes, with future support for detecting hidden or invisible content that may target AI-powered recruitment systems.

## The Problem

AI-powered recruitment tools are increasingly used to screen resumes automatically. This creates a new type of risk: a PDF resume could contain hidden text or instructions designed to manipulate an AI reader into approving a candidate regardless of their actual qualifications.

This project was inspired by discovering this type of issue in a real resume, where hidden instructions had been inserted to influence automated screening decisions.

## What CV Shield Does

CV Shield currently analyzes the text extracted from a PDF resume and flags potential red flags, such as:

- Suspicious instructions that resemble prompt injection attempts
- Instructions attempting to override previous instructions
- Instructions attempting to manipulate hiring recommendations

The project is also being developed toward detecting hidden or invisible PDF content, including:

- White-on-white text
- Zero-size text
- Off-page content
- Other potentially hidden text based on PDF structure and formatting

**Important:** CV Shield does not make hiring decisions. It only surfaces evidence for human review.

## Project Scope (MVP)

The first version focuses on:

1. Parsing PDF text with Python
2. Detecting suspicious text patterns
3. Generating structured scan reports
4. Producing JSON output for detected findings
5. Testing against fictional sample resumes

Future iterations will expand the project to include PDF structure analysis, AI-assisted analysis of suspicious instructions, and n8n integration for workflow automation.

## Tech Stack

- Python
- PDF parsing with pypdf
- Git & GitHub for version control
- n8n (planned, for later integration)

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

🚧 Work in progress. This project is being built and documented incrementally, including implementation challenges, testing, and dead ends along the way.

## Ethical Note

All test resumes used in this project are fictional or anonymized. No real candidate data is used or published.

CV Shield is intended to support human review, not automate hiring decisions or determine whether a candidate should be hired or rejected.
