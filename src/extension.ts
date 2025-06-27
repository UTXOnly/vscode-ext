import * as vscode from "vscode";
import { DatadogIntegrationFetcher } from "./integrationFetcher";
import { configureYamlSchemas } from "./helpers";

export function activate(context: vscode.ExtensionContext) {
  console.log("Datadog Integration Configuration extension is now active!");

  const integrationFetcher = new DatadogIntegrationFetcher();

  // Register command to update schemas
  let updateSchemasDisposable = vscode.commands.registerCommand(
    "datadog-integration-config.updateSchemas",
    async () => {
      try {
        await integrationFetcher.updateAllSchemas(context);
        await configureYamlSchemas(context);
        vscode.window.showInformationMessage(
          "Datadog integration schemas updated and configured successfully!"
        );
      } catch (error: any) {
        vscode.window.showErrorMessage(
          `Failed to update schemas: ${error.message}`
        );
      }
    }
  );

  // Register command to configure YAML schemas
  let configureSchemasDisposable = vscode.commands.registerCommand(
    "datadog-integration-config.configureSchemas",
    async () => {
      try {
        await configureYamlSchemas(context);
        vscode.window.showInformationMessage(
          "YAML schemas configured successfully!"
        );
      } catch (error: any) {
        vscode.window.showErrorMessage(
          `Failed to configure schemas: ${error.message}`
        );
      }
    }
  );

  context.subscriptions.push(
    updateSchemasDisposable,
    configureSchemasDisposable
  );

  // Initialize schemas on activation
  integrationFetcher
    .initializeSchemas(context)
    .then(async () => {
      try {
        await configureYamlSchemas(context);
      } catch (error: any) {
        console.error("Failed to configure YAML schemas:", error);
      }
    })
    .catch((error: any) => {
      console.error("Failed to initialize schemas:", error);
      vscode.window.showErrorMessage(
        "Failed to initialize Datadog schemas. Check the console for details."
      );
    });
}

export function deactivate() {}
