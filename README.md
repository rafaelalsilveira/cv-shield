# CV Shield

CV Shield is a document analysis tool designed to detect potentially hidden content and suspicious instructions in PDF resumes, including possible prompt injection attempts targeting AI-powered recruitment systems.

## The Problem

AI-powered recruitment tools are increasingly used to screen resumes automatically. This creates a new type of risk: a PDF resume could contain hidden text (invisible fonts, zero-size text, off-page content) designed to manipulate an AI reader into approving a candidate regardless of their actual qualifications.

This project was inspired by discovering this exact issue in a real resume, where hidden instructions had been inserted to influence automated screening decisions.

## What CV Shield Does

CV Shield analyzes a PDF resume and flags potential red flags, such as:

- Hidden or invisible text (white-on-white, zero font size, off-page positioning)
- Suspicious embedded instructions that resemble prompt injection attempts

**Important:** CV Shield does not make hiring decisions. It only surfaces evidence for human review.

## Project Scope (MVP)

The first version focuses on:

1. Parsing PDF text and formatting properties with Python
2. Detecting hidden or suspicious text patterns
3. Testing against sample fictional resumes
4. Generating a simple, structured report

Future iterations may include n8n integration for workflow automation and AI-based analysis of suspicious instructions.

## Tech Stack

- Python
- PDF parsing (library to be defined during development)
- Git & GitHub for version control
- n8n (planned, for later integration)

## Development Roadmap

- [ ] Step 1 — Project definition and initial setup
- [ ] Step 2 — Environment setup and PDF structure research
- [ ] Step 3 — First hidden-text detector
- [ ] Step 4 — AI-based analysis of suspicious instructions
- [ ] Step 5 — n8n integration and final report generation

## Status

🚧 Work in progress. This project is being built and documented incrementally, including challenges and dead ends along the way.

## Ethical Note

All test resumes used in this project are fictional or anonymized. No real candidate data is used or published.