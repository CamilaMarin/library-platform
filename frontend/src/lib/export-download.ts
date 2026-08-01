/**
 * Export download utilities for ARCO data access right.
 * Generates a downloadable JSON file from API export data.
 */

/**
 * Generates the export filename using the current date in ISO format.
 * @returns Filename in the format `entrelineas-datos-YYYY-MM-DD.json`
 */
export function generateExportFilename(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `entrelineas-datos-${date}.json`;
}

/**
 * Triggers a browser file download for JSON data.
 * Creates a Blob from the serialized data, generates a temporary object URL,
 * programmatically clicks a hidden `<a>` element, and revokes the URL.
 *
 * @param data - The data to serialize and download
 * @param filename - The filename for the downloaded file
 */
export function triggerJsonDownload(data: unknown, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();

  URL.revokeObjectURL(url);
}
