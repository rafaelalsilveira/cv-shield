# CV Shield

CV Shield is a Python-based document analysis tool designed to detect suspicious instructions and potential prompt injection attempts in PDF resumes.

The project explores how malicious or manipulative instructions embedded in resumes could affect AI-powered recruitment systems.

## The Problem

AI-powered recruitment systems are increasingly used to analyze and screen resumes.

This creates a potential security concern: a PDF resume may contain instructions designed to manipulate an AI system into changing how the document or candidate is evaluated.

CV Shield was created to investigate this type of risk by analyzing resume content and identifying suspicious patterns that may require human review.

## What CV Shield Does

CV Shield analyzes a PDF resume using two independent detectors:

1. **Suspicious pattern detector**: extracts the text and checks it against a list of known manipulative phrases, including:
   - Attempts to override previous instructions
   - Instructions designed to influence hiring recommendations
   - Attempts to automatically approve a resume
   - Attempts to bypass manual review

2. **Hidden text detector**: inspects each text fragment's font size, color and position on the page (not just its content), and flags:
   - Font sizes below 3pt (unreadable to a human)
   - Near-white text color (including pure white and colors very close to white, in both RGB and CMYK)
   - Text positioned outside the visible page area

This second detector can catch hidden instructions even when they avoid every known trigger phrase, since it looks at how the text is rendered rather than what it says.

**Important:** CV Shield does not make hiring decisions. It only identifies potential evidence for human review.

## Current MVP

The current MVP focuses on:

1. Extracting text from PDF resumes using Python and `pypdf`
2. Normalizing extracted text (collapsing line breaks and repeated whitespace) before matching
3. Detecting predefined suspicious text patterns
4. Extracting per-fragment style metadata (font size, color, position) from the PDF
5. Detecting hidden text based on font size, color and off-page position
6. Categorizing and merging findings from both detectors into a single report
7. Generating structured scan reports
8. Producing JSON output
9. Running automated tests against fictional resumes with different suspicious instruction and hidden-text patterns

## Test Cases

The project uses fictional resumes to validate the detection logic.

Current test cases include:

- Instruction override attempts
- Hiring recommendation manipulation
- Attempts to automatically approve a candidate
- Attempts to bypass manual review
- Attempts to manipulate technical evaluation results
- Patterns split across multiple lines by PDF text extraction
- Patterns spaced out with irregular whitespace
- Legitimate multiline resume text, to guard against false positives
- Hidden text at unreadable font sizes (white and near-white, RGB and CMYK)
- Hidden text positioned off the visible page, even when rendered in plain black
- A paraphrased manipulation attempt that avoids every known trigger phrase, caught only by the hidden text detector
- A legitimate resume with white text on a colored sidebar (a known false positive, documented below)

The test resumes are intentionally fictional and contain different suspicious instruction and hidden-text patterns to help validate and expand the detectors.

## Known Limitations & Lessons Learned

While testing against real PDF output (not just literal strings in unit tests), we found that `pypdf` extraction inserts line breaks exactly where the PDF renders a visual line break. A suspicious phrase spanning two lines in the PDF (e.g. "...passed with \nfull score") would not match a pattern written as a single-line string, since a substring comparison treats `\n` and a space as different characters.

This was fixed by normalizing whitespace (collapsing line breaks and repeated spaces into a single space) before pattern matching, and covered with a regression test built from real extracted PDF text rather than hand-written strings.

This also surfaced a deeper limitation: the phrase-based detector relies on matching a fixed list of known strings, so a paraphrased instruction avoiding those exact phrases will not be caught. This was addressed by adding a second, structural detector that inspects font size, color and position directly, independent of wording. It successfully catches a paraphrased test case that the phrase-based detector misses.

The structural detector introduces its own known limitation: it assumes the page background is white, so it only reasons about the text's own color, not what is behind it. A legitimate resume using white text on a colored sidebar (a common design pattern, demonstrated in `examples/test_colored_band_resume.pdf`) is currently flagged as a false positive. This is documented with a dedicated test marked `@expectedFailure`, so the suite records the limitation without treating it as a regression. Fixing this would require tracking background fills and rectangles drawn behind text, which is left for a future iteration.

We also found that `pypdf`'s reported text coordinates differed between versions (5.9.0 vs. 6.19.0) when testing the same PDF, which could silently change hidden-text detection results. The `pypdf` version is now pinned in `requirements.txt` to the version the detector was built and tested against.

## Tech Stack

- Python
- pypdf (version pinned in `requirements.txt`)
- unittest
- Git & GitHub
- n8n (planned)

## Development Roadmap

- [x] **Step 1: Project definition and initial setup**
- [x] **Step 2: Environment setup and basic PDF text extraction**
- [x] **Step 3: Initial suspicious-pattern detector**
- [x] **Step 4: Structured scan report generation**
- [x] **Step 5: JSON output and automated testing**
- [x] **Step 6: Hidden-text detection and PDF structure analysis**
- [ ] **Step 7: AI-assisted analysis of suspicious instructions**
- [ ] **Step 8: n8n integration and workflow automation**
- [ ] **Step 9: Expanded testing and validation**

## Status

🚧 **Work in progress**

CV Shield is being developed incrementally, with new detection rules, tests, experiments, and improvements added throughout the project.

## Ethical Considerations

All test resumes used in this project are fictional.

CV Shield is designed to support human review, not to make hiring decisions or determine whether a candidate should be hired or rejected.