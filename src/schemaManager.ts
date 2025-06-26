import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export class DatadogSchemaManager {
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    public async ensureSchemaDirectory(): Promise<string> {
        const schemaDir = path.join(this.context.extensionPath, 'schemas');
        
        if (!fs.existsSync(schemaDir)) {
            fs.mkdirSync(schemaDir, { recursive: true });
        }
        
        return schemaDir;
    }

    public async saveSchema(schemaName: string, schemaContent: any): Promise<string> {
        const schemaDir = await this.ensureSchemaDirectory();
        const schemaPath = path.join(schemaDir, `${schemaName}.json`);
        
        fs.writeFileSync(schemaPath, JSON.stringify(schemaContent, null, 2));
        
        return schemaPath;
    }

    public getSchemaPath(schemaName: string): string {
        return path.join(this.context.extensionPath, 'schemas', `${schemaName}.json`);
    }

    public schemaExists(schemaName: string): boolean {
        const schemaPath = this.getSchemaPath(schemaName);
        return fs.existsSync(schemaPath);
    }

    public async updateYamlSchemas(): Promise<void> {
        const config = vscode.workspace.getConfiguration('yaml');
        const schemas = config.get('schemas') as Record<string, string | string[]> || {};

        // Add Datadog agent configuration schema
        const datadogAgentSchema = this.getSchemaPath('datadog-agent');
        schemas[datadogAgentSchema] = [
            '**/datadog.yaml',
            '**/datadog.yml',
            '**/datadog-agent.yaml',
            '**/datadog-agent.yml',
            '**/datadog.conf.yaml',
            '**/datadog.conf.yml'
        ];

        // Update the configuration
        await config.update('schemas', schemas, vscode.ConfigurationTarget.Workspace);
    }
} 