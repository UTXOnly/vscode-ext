import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';
import * as yaml from 'js-yaml';

export class DatadogIntegrationFetcher {
    private readonly baseUrl = 'https://raw.githubusercontent.com/DataDog/integrations-core/master';
    private readonly integrations = [
        'disk',
        'cpu',
        'memory',
        'network',
        'postgres',
        'mysql',
        'redis',
        'nginx',
        'apache',
        'elasticsearch',
        'kafka',
        'rabbitmq',
        'mongodb',
        'cassandra',
        'docker',
        'kubernetes'
    ];

    public async initializeSchemas(context: vscode.ExtensionContext): Promise<void> {
        const schemaDir = path.join(context.extensionPath, 'schemas');
        
        if (!fs.existsSync(schemaDir)) {
            fs.mkdirSync(schemaDir, { recursive: true });
        }

        // Download schemas if they don't exist
        for (const integration of this.integrations) {
            const schemaPath = path.join(schemaDir, `${integration}.json`);
            if (!fs.existsSync(schemaPath)) {
                try {
                    await this.downloadIntegrationSchema(integration, schemaPath);
                } catch (error) {
                    console.error(`Failed to download schema for ${integration}:`, error);
                }
            }
        }

        // Show a message to the user about manual schema configuration
        vscode.window.showInformationMessage(
            'Datadog schemas downloaded. To enable autocompletion, add this to your VS Code settings: ' +
            'yaml.schemas with paths to the schemas in the extension folder.'
        );
    }

    public async updateAllSchemas(context: vscode.ExtensionContext): Promise<void> {
        const schemaDir = path.join(context.extensionPath, 'schemas');
        
        for (const integration of this.integrations) {
            const schemaPath = path.join(schemaDir, `${integration}.json`);
            try {
                // Force re-download even if schema exists
                await this.downloadIntegrationSchema(integration, schemaPath);
            } catch (error) {
                console.error(`Failed to update schema for ${integration}:`, error);
            }
        }

        vscode.window.showInformationMessage('Datadog integration schemas updated successfully!');
    }

    private async downloadIntegrationSchema(integration: string, schemaPath: string): Promise<void> {
        try {
            const specUrl = `${this.baseUrl}/${integration}/assets/configuration/spec.yaml`;
            console.log(`Downloading schema from: ${specUrl}`);
            
            const response = await axios.get(specUrl, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Datadog-VSCode-Extension/1.0'
                }
            });
            
            if (response.status === 200) {
                const yamlContent = response.data;
                const jsonSchema = this.convertDatadogSpecToJsonSchema(yamlContent, integration);
                
                fs.writeFileSync(schemaPath, JSON.stringify(jsonSchema, null, 2));
                console.log(`Downloaded and converted schema for ${integration}`);
            }
        } catch (error) {
            console.error(`Failed to download schema for ${integration}:`, error);
            // Create a basic schema as fallback
            const basicSchema = this.createBasicSchema(integration);
            fs.writeFileSync(schemaPath, JSON.stringify(basicSchema, null, 2));
        }
    }

    private convertDatadogSpecToJsonSchema(yamlContent: string, integration: string): any {
        try {
            const spec = yaml.load(yamlContent) as any;
            console.log(`Processing spec for ${integration}:`, JSON.stringify(spec, null, 2));
            
            const schema: any = {
                $schema: "http://json-schema.org/draft-07/schema#",
                title: `${spec.name || integration} Integration Configuration`,
                type: "object",
                properties: {},
                required: [],
                additionalProperties: false
            };

            // Parse DataDog spec format
            if (spec && spec.files && Array.isArray(spec.files)) {
                console.log(`Found ${spec.files.length} files in spec`);
                for (const file of spec.files) {
                    if (file.options && Array.isArray(file.options)) {
                        console.log(`Processing file options:`, JSON.stringify(file.options, null, 2));
                        this.processFileOptions(file.options, schema);
                    }
                }
            }

            console.log(`Final schema for ${integration}:`, JSON.stringify(schema, null, 2));

            // If no properties were found, add common Datadog integration structure
            if (Object.keys(schema.properties).length === 0) {
                console.log(`No properties found for ${integration}, using basic schema`);
                schema.properties = {
                    instances: {
                        type: "array",
                        items: {
                            type: "object",
                            properties: {
                                host: { type: "string", description: "Host to connect to" },
                                port: { type: "integer", description: "Port to connect to" },
                                username: { type: "string", description: "Username for authentication" },
                                password: { type: "string", description: "Password for authentication" }
                            }
                        },
                        description: "Integration instances configuration"
                    }
                };
                schema.required = ["instances"];
            }

            return schema;
        } catch (error) {
            console.error(`Failed to convert DataDog spec to JSON schema for ${integration}:`, error);
            return this.createBasicSchema(integration);
        }
    }

    private processFileOptions(options: any[], schema: any): void {
        for (const option of options) {
            if (option.template === 'init_config') {
                this.processInitConfig(option, schema);
            } else if (option.template === 'instances') {
                this.processInstances(option, schema);
            } else if (option.template === 'logs') {
                this.processLogs(option, schema);
            }
        }
    }

    private processInitConfig(option: any, schema: any): void {
        if (option.options && Array.isArray(option.options)) {
            const initConfigProps = this.extractPropertiesFromOptions(option.options);
            if (Object.keys(initConfigProps).length > 0) {
                schema.properties.init_config = {
                    type: "object",
                    properties: initConfigProps,
                    description: "Initial configuration for the integration"
                };
            }
        }
    }

    private processInstances(option: any, schema: any): void {
        if (option.options && Array.isArray(option.options)) {
            const instanceProps = this.extractPropertiesFromOptions(option.options);
            const requiredFields = this.getRequiredFields(option.options);
            
            if (Object.keys(instanceProps).length > 0) {
                schema.properties.instances = {
                    type: "array",
                    items: {
                        type: "object",
                        properties: instanceProps,
                        required: requiredFields
                    },
                    description: "Integration instances configuration"
                };
                schema.required.push("instances");
            }
        }
    }

    private processLogs(option: any, schema: any): void {
        schema.properties.logs = {
            type: "array",
            items: {
                type: "object",
                properties: {
                    type: { type: "string", description: "Log type (file, tcp, udp, etc.)" },
                    path: { type: "string", description: "Path to log file" },
                    source: { type: "string", description: "Log source identifier" }
                }
            },
            description: "Log collection configuration"
        };
    }

    private extractPropertiesFromOptions(options: any[]): any {
        const properties: any = {};
        
        for (const option of options) {
            if (option.name && option.value) {
                // Direct property
                const property = this.convertValueToProperty(option.value);
                if (option.description) {
                    property.description = option.description.trim();
                }
                properties[option.name] = property;
            } else if (option.template) {
                // Template reference - we'll handle common templates
                const templateProps = this.getTemplateProperties(option.template);
                Object.assign(properties, templateProps);
            }
        }
        
        return properties;
    }

    private getTemplateProperties(templateName: string): any {
        // Common template properties that are frequently used
        const templates: { [key: string]: any } = {
            'instances/http': {
                host: { type: "string", description: "Host to connect to" },
                port: { type: "integer", description: "Port to connect to" },
                username: { type: "string", description: "Username for authentication" },
                password: { type: "string", description: "Password for authentication" }
            },
            'instances/default': {
                disable_generic_tags: { 
                    type: "boolean", 
                    description: "Disable generic tags to avoid conflicts with other integrations",
                    default: false
                }
            },
            'init_config/http': {
                timeout: { type: "integer", description: "HTTP timeout in seconds", default: 10 },
                headers: { type: "object", description: "Additional HTTP headers" }
            },
            'init_config/default': {
                min_collection_interval: { 
                    type: "integer", 
                    description: "Minimum collection interval in seconds",
                    default: 15
                }
            }
        };
        
        return templates[templateName] || {};
    }

    private convertValueToProperty(value: any): any {
        const property: any = {};
        
        if (value.type) {
            property.type = value.type;
        }
        
        if (value.example !== undefined) {
            property.default = value.example;
        }
        
        if (value.display_default !== undefined) {
            property.default = value.display_default;
        }
        
        if (value.items) {
            property.items = this.convertValueToProperty(value.items);
        }
        
        if (value.properties) {
            property.type = "object";
            property.properties = {};
            for (const [key, propValue] of Object.entries(value.properties)) {
                property.properties[key] = this.convertValueToProperty(propValue as any);
            }
        }
        
        if (value.enum) {
            property.enum = value.enum;
        }
        
        if (value.minimum !== undefined) {
            property.minimum = value.minimum;
        }
        
        if (value.maximum !== undefined) {
            property.maximum = value.maximum;
        }
        
        return property;
    }

    private getRequiredFields(options: any[]): string[] {
        const required: string[] = [];
        
        for (const option of options) {
            if (option.required === true) {
                required.push(option.name);
            }
        }
        
        return required;
    }

    private createBasicSchema(integration: string): any {
        return {
            $schema: "http://json-schema.org/draft-07/schema#",
            title: `${integration} Integration Configuration`,
            type: "object",
            properties: {
                instances: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            host: {
                                type: "string",
                                description: "Host to connect to"
                            },
                            port: {
                                type: "integer",
                                description: "Port to connect to"
                            },
                            username: {
                                type: "string",
                                description: "Username for authentication"
                            },
                            password: {
                                type: "string",
                                description: "Password for authentication"
                            }
                        }
                    },
                    description: "Integration instances configuration"
                }
            },
            required: ["instances"]
        };
    }
} 