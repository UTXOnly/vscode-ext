import * as vscode from "vscode";

const INTEGRATIONS = ["disk", "redisdb"];

export const configureYamlSchemas = async (
  context: vscode.ExtensionContext
) => {
  // Try to configure yaml.schemas if the YAML extension is available
  try {
    const config = vscode.workspace.getConfiguration("yaml");
    const schemas =
      (config.get("schemas") as Record<string, string | string[]>) || {};

    // Add integration-specific schemas
    INTEGRATIONS.forEach((integration) => {
      const schemaPath = context.asAbsolutePath(`schemas/${integration}.json`);
      schemas[schemaPath] = `**/${integration}.d/conf.{yaml,yml}`;
    });

    // Update the configuration
    await config.update(
      "schemas",
      schemas,
      vscode.ConfigurationTarget.Workspace
    );
    console.log("YAML schemas configured successfully");
  } catch (error) {
    console.log(
      "YAML extension not available, schemas will need to be configured manually"
    );
    // Show instructions for manual configuration
    await showManualConfigurationInstructions(
      context.asAbsolutePath("schemas")
    );
  }
};

const showManualConfigurationInstructions = async (schemaDir: string) => {
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
    language: "markdown",
  });
  await vscode.window.showTextDocument(document);
};
