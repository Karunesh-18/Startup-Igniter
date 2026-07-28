# Document Templates

Place the following files here for docxtpl-based generation:

- `startup_report.docx` — Word template with Jinja2-style `{{variable}}` placeholders
  Variables available in the template context:
  - `{{ project_name }}`
  - `{{ project_tagline }}`
  - `{{ problem_statement }}`
  - `{{ target_audience }}`
  - `{{ value_proposition }}`
  - `{{ market_summary }}`
  - `{{ competitor_summary }}`
  - `{{ swot }}` (dict with strengths/weaknesses/opportunities/threats)
  - `{{ total_score }}`
  - `{{ lean_canvas }}` (dict)
  - `{{ ai_disclaimer }}`
  - `{{ legal_disclaimer }}`

If no template is found, the export router falls back to a plain python-docx document.

## Creating a DOCX template

1. Open Microsoft Word
2. Create your report layout with formatting
3. Insert placeholders as `{{ variable_name }}` where content should go
4. Save as `startup_report.docx`

Reference: https://docxtpl.readthedocs.io/
