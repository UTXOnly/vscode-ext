#!/usr/bin/env python3
"""
Datadog Configuration Template to JSON Schema Generator

This script parses the Datadog agent config_template.yaml file and generates
a JSON schema based on the parameter definitions found in the comments.
"""

import re
import sys
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class DatadogSchemaGenerator:
    def __init__(self):
        self.schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Datadog Agent Configuration",
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        
    def parse_param_comment(self, comment: str) -> Optional[Dict[str, Any]]:
        """
        Parse a parameter comment line to extract parameter information.
        
        Expected format: ## @param param_name - type - optional/required - default: value
        """
        # Match the parameter definition pattern
        param_pattern = r'## @param (\w+) - ([^-]+) - (optional|required)(?: - default: (.+))?'
        match = re.match(param_pattern, comment.strip())
        
        if not match:
            return None
            
        param_name, param_type, required_flag, default_value = match.groups()
        
        return {
            "name": param_name,
            "type": param_type.strip(),
            "required": required_flag == "required",
            "default": default_value.strip() if default_value else None,
            "description": ""
        }
    
    def parse_section_comment(self, comment: str) -> Optional[str]:
        """
        Parse section comment to extract section name.
        
        Expected format: ## @param section_name - custom object - optional
        """
        section_pattern = r'## @param (\w+) - custom object - optional'
        match = re.match(section_pattern, comment.strip())
        
        if match:
            return match.group(1)
        return None
    
    def yaml_type_to_json_type(self, yaml_type: str) -> str:
        """Convert YAML type descriptions to JSON schema types."""
        yaml_type = yaml_type.lower().strip()
        
        type_mapping = {
            "string": "string",
            "boolean": "boolean",
            "integer": "integer",
            "number": "number",
            "list of strings": "array",
            "list of key:value elements": "array",
            "list of custom objects": "array",
            "space separated list of strings": "array",
            "list of key:value strings": "object",
            "custom object": "object",
            "duration": "string",
            "map": "object"
        }
        
        return type_mapping.get(yaml_type, "string")
    
    def get_array_items_schema(self, yaml_type: str) -> Dict[str, Any]:
        """Generate schema for array items based on YAML type."""
        yaml_type = yaml_type.lower().strip()
        
        if "strings" in yaml_type:
            return {"type": "string"}
        elif "key:value" in yaml_type:
            return {"type": "string"}
        elif "custom objects" in yaml_type:
            return {"type": "object"}
        else:
            return {"type": "string"}
    
    def parse_default_value(self, default_str: str) -> Any:
        """Parse default value string into appropriate type."""
        if not default_str:
            return None
            
        default_str = default_str.strip()
        
        # Handle boolean values
        if default_str.lower() in ["true", "false"]:
            return default_str.lower() == "true"
        
        # Handle numeric values
        try:
            if "." in default_str:
                return float(default_str)
            else:
                return int(default_str)
        except ValueError:
            pass
        
        # Handle quoted strings
        if default_str.startswith('"') and default_str.endswith('"'):
            return default_str[1:-1]
        if default_str.startswith("'") and default_str.endswith("'"):
            return default_str[1:-1]
        
        # Handle special values
        if default_str in ["<HOSTNAME_NAME>", "<ENDPOINT>:<PORT>", "<TAG_KEY>:<TAG_VALUE>"]:
            return None
        
        return default_str
    
    def extract_description(self, lines: List[str], start_idx: int) -> str:
        """Extract description from comment lines following a parameter definition."""
        description_lines = []
        i = start_idx + 1
        
        while i < len(lines) and lines[i].strip().startswith("##"):
            line = lines[i].strip()
            if line.startswith("## @param") or line.startswith("## @env"):
                break
            if line.startswith("##"):
                # Remove ## and clean up
                desc_line = line[2:].strip()
                if desc_line:
                    description_lines.append(desc_line)
            i += 1
        
        return " ".join(description_lines)
    
    def parse_template_file(self, template_path: str) -> Dict[str, Any]:
        """Parse the config template file and generate JSON schema."""
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_section = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and template directives
            if not line or line.startswith("{{"):
                i += 1
                continue
            
            # Check for section comments
            if line.startswith("## @param") and "custom object" in line:
                section_name = self.parse_section_comment(line)
                if section_name:
                    current_section = section_name
                    # Add section to schema
                    self.schema["properties"][section_name] = {
                        "type": "object",
                        "properties": {},
                        "description": f"Configuration for {section_name}"
                    }
                i += 1
                continue
            
            # Check for parameter comments
            if line.startswith("## @param") and "custom object" not in line:
                param_info = self.parse_param_comment(line)
                if param_info:
                    # Extract description from following lines
                    param_info["description"] = self.extract_description(lines, i)
                    
                    # Determine where to add this property
                    if current_section:
                        target_props = self.schema["properties"][current_section]["properties"]
                    else:
                        target_props = self.schema["properties"]
                    
                    # Convert to JSON schema format
                    json_type = self.yaml_type_to_json_type(param_info["type"])
                    property_schema = {
                        "type": json_type,
                        "description": param_info["description"]
                    }
                    
                    # Add default value if present
                    if param_info["default"] is not None:
                        default_val = self.parse_default_value(param_info["default"])
                        if default_val is not None:
                            property_schema["default"] = default_val
                    
                    # Handle arrays
                    if json_type == "array":
                        property_schema["items"] = self.get_array_items_schema(param_info["type"])
                        if "default" not in property_schema:
                            property_schema["default"] = []
                    
                    # Handle objects
                    if json_type == "object":
                        property_schema["additionalProperties"] = True
                    
                    target_props[param_info["name"]] = property_schema
                    
                    # Mark as required if needed
                    if param_info["required"]:
                        if current_section:
                            if "required" not in self.schema["properties"][current_section]:
                                self.schema["properties"][current_section]["required"] = []
                            self.schema["properties"][current_section]["required"].append(param_info["name"])
                        else:
                            if "required" not in self.schema:
                                self.schema["required"] = []
                            self.schema["required"].append(param_info["name"])
            
            i += 1
        
        return self.schema
    
    def generate_schema(self, template_path: str, output_path: str = None) -> str:
        """Generate JSON schema from template file."""
        schema = self.parse_template_file(template_path)
        
        # Convert to JSON string
        schema_json = json.dumps(schema, indent=2)
        
        # Write to file if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(schema_json)
            print(f"Schema written to {output_path}")
        
        return schema_json


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_datadog_schema.py <template_path> [output_path]")
        print("Example: python generate_datadog_schema.py pkg/config/config_template.yaml datadog_schema.json")
        sys.exit(1)
    
    template_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(template_path).exists():
        print(f"Error: Template file '{template_path}' not found")
        sys.exit(1)
    
    generator = DatadogSchemaGenerator()
    
    try:
        schema_json = generator.generate_schema(template_path, output_path)
        if not output_path:
            print(schema_json)
    except Exception as e:
        print(f"Error generating schema: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 