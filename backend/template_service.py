from jinja2 import Environment, BaseLoader, TemplateError
from typing import Dict, Any, List
import json
from datetime import datetime
from models import Template, RFPRequest, RFPQuestion
from sqlalchemy.orm import Session

class StringTemplateLoader(BaseLoader):
    def __init__(self, template_string: str):
        self.template_string = template_string
    
    def get_source(self, environment, template):
        return self.template_string, None, lambda: True

class TemplateService:
    def __init__(self):
        self.env = Environment()
        self.env.filters['dateformat'] = self._date_format_filter
        self.env.filters['currency'] = self._currency_filter
        self.env.filters['titlecase'] = lambda s: s.title() if s else ""
    
    def _date_format_filter(self, date_value, format_string='%Y-%m-%d'):
        if isinstance(date_value, str):
            return date_value
        return date_value.strftime(format_string) if date_value else ""
    
    def _currency_filter(self, value, currency='USD'):
        try:
            return f"{currency} {float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def render_rfp_response(self, 
                          template_content: str, 
                          rfp_data: Dict[str, Any], 
                          branding_data: Dict[str, Any] = None) -> str:
        try:
            template = Environment(loader=StringTemplateLoader(template_content)).get_template("")
            
            context = {
                'rfp': rfp_data,
                'branding': branding_data or {},
                'generated_at': datetime.now(),
                'current_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            return template.render(**context)
        except TemplateError as e:
            raise ValueError(f"Template rendering error: {str(e)}")
    
    def get_default_html_template(self) -> str:
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ rfp.title }} - Response</title>
    <style>
        body {
            font-family: {{ branding.font_family or 'Arial, sans-serif' }};
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: {{ branding.text_color or '#333' }};
        }
        .header {
            background-color: {{ branding.primary_color or '#007bff' }};
            color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .company-logo {
            max-height: 60px;
            margin-bottom: 10px;
        }
        .rfp-title {
            font-size: 24px;
            margin: 0;
            font-weight: bold;
        }
        .rfp-meta {
            margin-top: 10px;
            opacity: 0.9;
        }
        .question-section {
            margin-bottom: 30px;
            padding: 20px;
            border-left: 4px solid {{ branding.accent_color or '#28a745' }};
            background-color: #f8f9fa;
        }
        .question {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
            color: {{ branding.primary_color or '#007bff' }};
        }
        .answer {
            margin-left: 20px;
            line-height: 1.8;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid {{ branding.primary_color or '#007bff' }};
            text-align: center;
            color: #666;
        }
        .generated-info {
            font-size: 12px;
            color: #999;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        {% if branding.logo_url %}
        <img src="{{ branding.logo_url }}" alt="{{ branding.company_name or 'Company Logo' }}" class="company-logo">
        {% endif %}
        <h1 class="rfp-title">{{ rfp.title }}</h1>
        <div class="rfp-meta">
            {% if rfp.client_name %}<strong>Client:</strong> {{ rfp.client_name }}<br>{% endif %}
            {% if rfp.due_date %}<strong>Due Date:</strong> {{ rfp.due_date | dateformat }}<br>{% endif %}
            <strong>Generated:</strong> {{ current_date }}
        </div>
    </div>

    <div class="content">
        {% for question in rfp.questions %}
        <div class="question-section">
            <div class="question">{{ loop.index }}. {{ question.question_text }}</div>
            <div class="answer">
                {% if question.generated_answer %}
                    {{ question.generated_answer | replace('\n', '<br>') | safe }}
                {% else %}
                    <em>Answer pending review</em>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="footer">
        {% if branding.company_name %}
        <p><strong>{{ branding.company_name }}</strong></p>
        {% endif %}
        {% if branding.contact_email %}
        <p>Contact: {{ branding.contact_email }}</p>
        {% endif %}
        {% if branding.website %}
        <p>Website: {{ branding.website }}</p>
        {% endif %}
        
        <div class="generated-info">
            Generated on {{ generated_at.strftime('%Y-%m-%d at %H:%M:%S') }} using RFP SaaS Platform
        </div>
    </div>
</body>
</html>
        """
    
    def get_default_markdown_template(self) -> str:
        return """
# {{ rfp.title }}

{% if rfp.client_name %}**Client:** {{ rfp.client_name }}{% endif %}
{% if rfp.due_date %}**Due Date:** {{ rfp.due_date | dateformat }}{% endif %}
**Generated:** {{ current_date }}

---

{% for question in rfp.questions %}
## {{ loop.index }}. {{ question.question_text }}

{% if question.generated_answer %}
{{ question.generated_answer }}
{% else %}
*Answer pending review*
{% endif %}

---
{% endfor %}

{% if branding.company_name %}
## Contact Information

**{{ branding.company_name }}**
{% if branding.contact_email %}Email: {{ branding.contact_email }}{% endif %}
{% if branding.website %}Website: {{ branding.website }}{% endif %}
{% endif %}

*Generated on {{ generated_at.strftime('%Y-%m-%d at %H:%M:%S') }} using RFP SaaS Platform*
        """
    
    def create_default_templates(self, db: Session, tenant_id: str, user_id: str):
        html_template = Template(
            tenant_id=tenant_id,
            name="Default HTML Template",
            template_content=self.get_default_html_template(),
            template_type="html",
            is_default=True,
            created_by=user_id
        )
        
        markdown_template = Template(
            tenant_id=tenant_id,
            name="Default Markdown Template", 
            template_content=self.get_default_markdown_template(),
            template_type="markdown",
            is_default=False,
            created_by=user_id
        )
        
        db.add(html_template)
        db.add(markdown_template)
        db.commit()
        
        return [html_template, markdown_template]

template_service = TemplateService()