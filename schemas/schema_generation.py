import os
import yaml
import json
import requests

INTEGRATIONS_CORE_SOURCE = "https://raw.githubusercontent.com/DataDog/integrations-core/refs/heads/master"
SCHEMA_OUTPUT_DIRECTORY = "./schema_files"
SPEC_FILE_PATH = "/assets/configuration/spec.yaml"

def rec_generate_nodes(current_node):
    """ Recursively iterates down the Datadog spec yaml tree, generating the JSON schema nodes 
    """
    if not "options" in current_node:
        return

    current_properties = {}

    for property in current_node["options"]:
        try:
            prop_name = property["name"] 
        except:
            # There is an 'overrides' property I'm going to ignore for now cause I don't know what it does
            continue

        current_properties[prop_name] = {}

        # Parsing out the properties from the spec yaml:
        if "description" in property:
            current_properties[prop_name]["description"] = str(property["description"])
            
        if "value" in property:
            if "example" in property["value"] and property["value"]["example"]:
                current_properties[prop_name]["example"] = property["value"]["example"]
            
            if "type" in property["value"]:
                current_properties[prop_name]["type"] = property["value"]["type"]

        # Make a recursive call downward if there is a list of subproperties:
        if "options" in property:
            inner_properties = rec_generate_nodes(property) # not tail recursive but im lazy :(
            current_properties[prop_name]["properties"] = inner_properties
            current_properties[prop_name]["type"] = "object"

    return current_properties

def generate_json_spec(integration_name, output_directory = SCHEMA_OUTPUT_DIRECTORY):
    """ Generates a json spec from a datadog spec yaml file
    """

    url_path = f"{INTEGRATIONS_CORE_SOURCE}/{integration_name}/{SPEC_FILE_PATH}"
    response = requests.get(url_path)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Load the YAML content
    config_spec = yaml.safe_load(response.text)    
    input_spec = {}

    # Drill down to just the relevant fields:
    for spec_file in config_spec["files"]:
        if f"{integration_name}.yaml" == spec_file["name"]:
            input_spec = spec_file["options"]

    # Breaking out the spec file into its two main template sections, init_config, instances
    init_config, instances = input_spec[0], input_spec[1]
    
    # Running the instances json properties generation
    init_config_properties = rec_generate_nodes(init_config)
    instance_properties = rec_generate_nodes(instances)
    
    output_json = {
        "$schema": "https://json-schema.org/draft/2020-12/schema#",
        "title": f"{integration_name} integration schema",
        "type": "object",
        "properties": {
            "init_config": {
                "type": "object",
                "properties": init_config_properties,
            },
            "instances": {
                "type": "object",
                "properties": instance_properties,
            },
        },
        "required": ["init_config", "instances"],
        "additionalProperties": False
    }

    #pprint.pprint(output_json)
    # Writing the output.json
    with open(os.path.join(SCHEMA_OUTPUT_DIRECTORY, f"{integration_name}.json"), "w") as fp_out:
        json.dump(output_json, fp_out, indent=2)

if __name__ == '__main__':
    generate_json_spec("disk")
    generate_json_spec("redisdb")
