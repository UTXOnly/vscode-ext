#!/usr/bin/env python3
"""
Datadog Configuration Template to JSON Schema Generator

This script parses the Datadog agent config_template.yaml file and generates
a JSON schema based on the parameter definitions found in the comments.
"""

import re
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


class DatadogSchemaGenerator:
    def __init__(self, debug: bool = False, log_file: str = None):
        self.debug = debug
        self.schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Datadog Agent Configuration",
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
        
        # Set up logging
        if debug:
            if log_file:
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file, mode='w'),
                        logging.StreamHandler(sys.stdout)
                    ]
                )
            else:
                logging.basicConfig(
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s'
                )
        
    def log(self, message: str):
        """Debug logging function."""
        if self.debug:
            logging.debug(message)
        
    def parse_param_comment(self, comment: str) -> Optional[Dict[str, Any]]:
        """
        Parse a parameter comment line to extract parameter information.
        
        Expected format: ## @param param_name - type - optional/required - default: value
        """
        self.log(f"Parsing param comment: {comment}")
        
        # Match the parameter definition pattern
        param_pattern = r'## @param (\w+) - ([^-]+) - (optional|required)(?: - default: (.+))?'
        match = re.match(param_pattern, comment.strip())
        
        if not match:
            self.log(f"No match found for param pattern in: {comment}")
            return None
            
        param_name, param_type, required_flag, default_value = match.groups()
        
        result = {
            "name": param_name,
            "type": param_type.strip(),
            "required": required_flag == "required",
            "default": default_value.strip() if default_value else None,
            "description": ""
        }
        
        self.log(f"Parsed param: {result}")
        return result
    
    def parse_section_comment(self, comment: str) -> Optional[str]:
        """
        Parse section comment to extract section name.
        
        Expected format: ## @param section_name - custom object - optional
        """
        self.log(f"Parsing section comment: {comment}")
        
        section_pattern = r'## @param (\w+) - custom object - optional'
        match = re.match(section_pattern, comment.strip())
        
        if match:
            section_name = match.group(1)
            self.log(f"Found section: {section_name}")
            return section_name
        else:
            self.log(f"No section match found in: {comment}")
        return None
    
    def yaml_type_to_json_type(self, yaml_type: str) -> str:
        """Convert YAML type descriptions to JSON schema types."""
        yaml_type = yaml_type.lower().strip()
        self.log(f"Converting YAML type '{yaml_type}' to JSON type")
        
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
        
        json_type = type_mapping.get(yaml_type, "string")
        self.log(f"Converted '{yaml_type}' to '{json_type}'")
        return json_type
    
    def get_array_items_schema(self, yaml_type: str) -> Dict[str, Any]:
        """Generate schema for array items based on YAML type."""
        yaml_type = yaml_type.lower().strip()
        self.log(f"Getting array items schema for type: {yaml_type}")
        
        if "strings" in yaml_type:
            result = {"type": "string"}
        elif "key:value" in yaml_type:
            result = {"type": "string"}
        elif "custom objects" in yaml_type:
            result = {"type": "object"}
        else:
            result = {"type": "string"}
            
        self.log(f"Array items schema: {result}")
        return result
    
    def parse_default_value(self, default_str: str) -> Any:
        """Parse default value string into appropriate type."""
        self.log(f"Parsing default value: '{default_str}'")
        
        if not default_str:
            self.log("No default value provided")
            return None
            
        default_str = default_str.strip()
        
        # Handle boolean values
        if default_str.lower() in ["true", "false"]:
            result = default_str.lower() == "true"
            self.log(f"Parsed boolean default: {result}")
            return result
        
        # Handle numeric values
        try:
            if "." in default_str:
                result = float(default_str)
                self.log(f"Parsed float default: {result}")
                return result
            else:
                result = int(default_str)
                self.log(f"Parsed integer default: {result}")
                return result
        except ValueError:
            pass
        
        # Handle quoted strings
        if default_str.startswith('"') and default_str.endswith('"'):
            result = default_str[1:-1]
            self.log(f"Parsed quoted string default: {result}")
            return result
        if default_str.startswith("'") and default_str.endswith("'"):
            result = default_str[1:-1]
            self.log(f"Parsed single-quoted string default: {result}")
            return result
        
        # Handle special values
        if default_str in ["<HOSTNAME_NAME>", "<ENDPOINT>:<PORT>", "<TAG_KEY>:<TAG_VALUE>"]:
            self.log(f"Special value detected: {default_str}")
            return None
        
        self.log(f"Using string default as-is: {default_str}")
        return default_str
    
    def extract_description(self, lines: List[str], start_idx: int) -> str:
        """Extract description from comment lines following a parameter definition."""
        self.log(f"Extracting description starting from line {start_idx}")
        
        description_lines = []
        i = start_idx + 1
        
        while i < len(lines) and lines[i].strip().startswith("##"):
            line = lines[i].strip()
            self.log(f"Processing description line {i}: {line}")
            
            if line.startswith("## @param") or line.startswith("## @env"):
                self.log("Found next parameter or env directive, stopping description extraction")
                break
            if line.startswith("##"):
                # Remove ## and clean up
                desc_line = line[2:].strip()
                if desc_line:
                    description_lines.append(desc_line)
                    self.log(f"Added description line: {desc_line}")
            i += 1
        
        description = " ".join(description_lines)
        self.log(f"Final description: {description}")
        return description
    
    def parse_template_file(self, template_path: str) -> Dict[str, Any]:
        """Parse the config template file and generate JSON schema."""
        self.log(f"Starting to parse template file: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.log(f"Read {len(lines)} lines from template file")
        
        current_section = None
        section_stack = []  # Track nested sections
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            original_line = lines[i].rstrip()
            indent_level = len(original_line) - len(original_line.lstrip())
            
            self.log(f"Line {i} (indent: {indent_level}): '{line}'")
            
            # Skip empty lines
            if not line:
                self.log(f"Skipping empty line {i}")
                i += 1
                continue
            
            # Handle template directives
            if line.startswith("{{"):
                self.log(f"Found template directive at line {i}: {line}")
                if "end" in line:
                    # End of a template block, pop the section stack
                    if section_stack:
                        popped_section = section_stack.pop()
                        self.log(f"End of template block, popped section: {popped_section}")
                        current_section = section_stack[-1] if section_stack else None
                i += 1
                continue
            
            # Check for section comments
            if line.startswith("## @param") and "custom object" in line:
                self.log(f"Found section comment at line {i}")
                section_name = self.parse_section_comment(line)
                if section_name:
                    current_section = section_name
                    section_stack.append(section_name)
                    # Add section to schema
                    self.schema["properties"][section_name] = {
                        "type": "object",
                        "properties": {},
                        "description": f"Configuration for {section_name}"
                    }
                    self.log(f"Added section '{section_name}' to schema. Stack: {section_stack}")
                i += 1
                continue
            
            # Check for parameter comments
            if line.startswith("## @param") and "custom object" not in line:
                self.log(f"Found parameter comment at line {i}")
                param_info = self.parse_param_comment(line)
                if param_info:
                    # Extract description from following lines
                    param_info["description"] = self.extract_description(lines, i)
                    
                    # Check if this parameter should be in the current section
                    # by looking at the indentation of the actual parameter line
                    param_line_indent = self.find_parameter_line_indent(lines, i)
                    self.log(f"Parameter '{param_info['name']}' has indent level: {param_line_indent}")
                    
                    # Determine the target section based on indentation and current section
                    target_section = self.determine_target_section(current_section, param_line_indent, section_stack)
                    
                    # If we couldn't determine the section from indentation, try context
                    if not target_section and param_line_indent > 0:
                        context_section = self.find_section_context(lines, i)
                        if context_section:
                            target_section = context_section
                            self.log(f"Using context to determine section: {target_section}")
                    
                    self.log(f"Target section for '{param_info['name']}': {target_section}")
                    
                    if target_section:
                        target_props = self.schema["properties"][target_section]["properties"]
                        self.log(f"Adding '{param_info['name']}' to section '{target_section}' (indent: {param_line_indent})")
                    else:
                        target_props = self.schema["properties"]
                        self.log(f"Adding '{param_info['name']}' to root level (indent: {param_line_indent})")
                    
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
                        self.log(f"Added additionalProperties for object type: {param_info['name']}")
                    
                    target_props[param_info["name"]] = property_schema
                    self.log(f"Added property '{param_info['name']}' with schema: {json.dumps(property_schema, indent=2)}")
                    
                    # Mark as required if needed
                    if param_info["required"]:
                        if target_section:
                            if "required" not in self.schema["properties"][target_section]:
                                self.schema["properties"][target_section]["required"] = []
                            self.schema["properties"][target_section]["required"].append(param_info["name"])
                            self.log(f"Marked '{param_info['name']}' as required in section '{target_section}'")
                        else:
                            if "required" not in self.schema:
                                self.schema["required"] = []
                            self.schema["required"].append(param_info["name"])
                            self.log(f"Marked '{param_info['name']}' as required at root level")
            
            i += 1
        
        self.log(f"Finished parsing. Final schema: {json.dumps(self.schema, indent=2)}")
        return self.schema
    
    def find_parameter_line_indent(self, lines: List[str], param_comment_idx: int) -> int:
        """Find the indentation level of the actual parameter line following a parameter comment."""
        i = param_comment_idx + 1
        
        # Skip description lines
        while i < len(lines) and lines[i].strip().startswith("##"):
            i += 1
        
        # Look for the actual parameter line (non-comment, non-empty)
        while i < len(lines):
            line = lines[i].strip()
            if line and not line.startswith("##") and not line.startswith("{{"):
                # Found the parameter line
                original_line = lines[i].rstrip()
                indent_level = len(original_line) - len(original_line.lstrip())
                self.log(f"Found parameter line at index {i} with indent {indent_level}: '{line}'")
                return indent_level
            i += 1
        
        # If no parameter line found, assume root level
        self.log("No parameter line found, assuming root level (indent 0)")
        return 0
    
    def determine_target_section(self, current_section: str, param_indent: int, section_stack: List[str]) -> str:
        """Determine which section a parameter should belong to based on indentation and section stack."""
        self.log(f"Determining target section. Current: {current_section}, indent: {param_indent}, stack: {section_stack}")
        
        # If no indentation, it's at root level
        if param_indent == 0:
            self.log("No indentation, placing at root level")
            return None
        
        # If we have a current section and the parameter is indented, it belongs to that section
        if current_section and param_indent > 0:
            self.log(f"Parameter belongs to current section: {current_section}")
            return current_section
        
        # If no current section but we have indentation, this might be an error
        self.log("No current section but parameter is indented, placing at root level")
        return None
    
    def find_section_context(self, lines: List[str], param_idx: int) -> str:
        """Find the section context by looking backwards from the parameter."""
        self.log(f"Looking for section context around line {param_idx}")
        
        # Look backwards for the most recent section definition
        i = param_idx - 1
        while i >= 0:
            line = lines[i].strip()
            
            # Check for section comments
            if line.startswith("## @param") and "custom object" in line:
                section_name = self.parse_section_comment(line)
                if section_name:
                    self.log(f"Found section context: {section_name}")
                    return section_name
            
            # Check for template directives that might indicate section boundaries
            if line.startswith("{{") and "end" in line:
                self.log("Found template end, stopping section search")
                break
                
            i -= 1
        
        self.log("No section context found")
        return None
    
    def generate_schema(self, template_path: str, output_path: str = None) -> str:
        """Generate JSON schema from template file."""
        self.log(f"Generating schema from {template_path}")
        schema = self.parse_template_file(template_path)
        
        # Convert to JSON string
        schema_json = json.dumps(schema, indent=2)
        
        # Write to file if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(schema_json)
            self.log(f"Schema written to {output_path}")
        
        return schema_json


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_datadog_schema.py <template_path> [output_path] [--debug] [--log-file <log_file>]")
        print("Example: python generate_datadog_schema.py pkg/config/config_template.yaml datadog_schema.json --debug --log-file debug.log")
        sys.exit(1)
    
    template_path = sys.argv[1]
    output_path = None
    debug = False
    log_file = False
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--debug':
            debug = True
        elif arg == '--log-file' and i + 1 < len(sys.argv):
            log_file = sys.argv[i + 1]
            i += 1
        elif not arg.startswith('--') and output_path is None:
            output_path = arg
        i += 1
    
    if not Path(template_path).exists():
        print(f"Error: Template file '{template_path}' not found")
        sys.exit(1)
    
    generator = DatadogSchemaGenerator(debug=debug, log_file=log_file)
    
    try:
        schema_json = generator.generate_schema(template_path, output_path)
        if not output_path:
            print(schema_json)
    except Exception as e:
        print(f"Error generating schema: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 