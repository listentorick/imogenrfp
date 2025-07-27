from jinja2 import Environment, BaseLoader, TemplateError
from typing import Dict, Any, List
import json
from datetime import datetime
from models import Template
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
    
    def render_template(self, 
                       template_content: str, 
                       context_data: Dict[str, Any]) -> str:
        try:
            template = Environment(loader=StringTemplateLoader(template_content)).get_template("")
            return template.render(**context_data)
        except TemplateError as e:
            raise ValueError(f"Template rendering error: {str(e)}")
    
    def get_default_html_template(self) -> str:
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .header {
            background-color: #007bff;
            color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .content {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #007bff;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Document Title</h1>
    </div>
    <div class="content">
        <p>Document content goes here.</p>
    </div>
    <div class="footer">
        <p>Generated on {{ current_date }}</p>
    </div>
</body>
</html>
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
        
        db.add(html_template)
        db.commit()
        
        return [html_template]

template_service = TemplateService()