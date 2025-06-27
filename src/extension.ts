import * as vscode from 'vscode';
import { DatadogIntegrationFetcher } from './integrationFetcher';

export function activate(context: vscode.ExtensionContext) {
    console.log('Datadog Integration Configuration extension is now active!');

    const integrationFetcher = new DatadogIntegrationFetcher();

    // Register command to update schemas
    let updateSchemasDisposable = vscode.commands.registerCommand('datadog-integration-config.updateSchemas', async () => {
        try {
            await integrationFetcher.updateAllSchemas(context);
            await configureYamlSchemas(context);
            vscode.window.showInformationMessage('Datadog integration schemas updated and configured successfully!');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to update schemas: ${error.message}`);
        }
    });

    // Register command to configure YAML schemas
    let configureSchemasDisposable = vscode.commands.registerCommand('datadog-integration-config.configureSchemas', async () => {
        try {
            await configureYamlSchemas(context);
            vscode.window.showInformationMessage('YAML schemas configured successfully!');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to configure schemas: ${error.message}`);
        }
    });

    context.subscriptions.push(updateSchemasDisposable, configureSchemasDisposable);

    // Initialize schemas on activation
    integrationFetcher.initializeSchemas(context).then(async () => {
        try {
            await configureYamlSchemas(context);
        } catch (error: any) {
            console.error('Failed to configure YAML schemas:', error);
        }
    }).catch((error: any) => {
        console.error('Failed to initialize schemas:', error);
        vscode.window.showErrorMessage('Failed to initialize Datadog schemas. Check the console for details.');
    });
}

async function configureYamlSchemas(context: vscode.ExtensionContext): Promise<void> {
    // Try to configure yaml.schemas if the YAML extension is available
    try {
        const config = vscode.workspace.getConfiguration('yaml');
        const schemas = config.get('schemas') as Record<string, string | string[]> || {};

        const integrations = [
            'disk', 'redis'
        ];

        // Add integration-specific schemas
        integrations.forEach(integration => {
            const schemaPath = context.asAbsolutePath(`schemas/${integration}.json`);
            schemas[schemaPath] = [
                `**/${integration}.yaml`,
                `**/${integration}.yml`,
                `**/conf.d/${integration}.d/conf.yaml`,
                `**/conf.d/${integration}.d/conf.yml`
            ];
        });

        // Update the configuration
        await config.update('schemas', schemas, vscode.ConfigurationTarget.Workspace);
        console.log('YAML schemas configured successfully');
    } catch (error) {
        console.log('YAML extension not available, schemas will need to be configured manually');
        // Show instructions for manual configuration
        const schemaDir = context.asAbsolutePath('schemas');
        const instructions = `To enable YAML autocompletion for Datadog integrations, you need to:

1. Install the YAML extension (vscode-yaml) from the marketplace
2. Add this to your VS Code settings.json:

{
    "yaml.schemas": {
        "${schemaDir}/disk.json": ["**/conf.d/disk.yaml", "**/conf.d/disk.yml"],
        "${schemaDir}/redis.json": ["**/conf.d/redis.yaml", "**/conf.d/redis.yml"]
    }
}

The schemas are located in: ${schemaDir}`;

        const document = await vscode.workspace.openTextDocument({
            content: instructions,
            language: 'markdown'
        });
        await vscode.window.showTextDocument(document);
    }
}

export function deactivate() {} 