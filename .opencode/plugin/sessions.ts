/**
 * OpenCode Session Tools
 * Simplified to match AmpCode's find_thread / read_thread
 *
 * Core tools:
 * - find_sessions: Search sessions by keyword (like AmpCode's find_thread)
 * - read_session: Read session messages (like AmpCode's read_thread)
 */

import type { Plugin } from "@opencode-ai/plugin";
import { tool } from "@opencode-ai/plugin/tool";

export const SessionsPlugin: Plugin = async ({ client }) => {
	return {
		tool: {
			/** Like AmpCode's find_thread */
			find_sessions: tool({
				description: `Search sessions by keyword.
	
Example:
find_sessions({ query: "auth", limit: 5 })`,
				args: {
					query: tool.schema.string().describe("Search query"),
					limit: tool.schema
						.number()
						.optional()
						.describe("Max results (default: 10)"),
				},
				async execute(args: { query: string; limit?: number }) {
					const sessions = await client.session.list();
					const results: string[] = [];
					let searched = 0;
					const searchLimit = args.limit || 10;

					if (!sessions.data) return "No sessions found.";

					for (const session of sessions.data) {
						if (results.length >= searchLimit) break;

						try {
							const messages = await client.session.messages({
								path: { id: session.id },
							});
							const messageData = messages.data;
							if (!messageData) continue;

							const matches = messageData.filter(
								(m: any) =>
									m.info &&
									JSON.stringify(m.info)
										.toLowerCase()
										.includes(args.query.toLowerCase()),
							);

							if (matches.length > 0) {
								const excerpt = extractContent(matches[0].info) || "";
								results.push(
									`**${session.id}** - ${session.title || "Untitled"}\n   Matches: ${matches.length}\n   ${excerpt.substring(0, 100)}...`,
								);
							}

							searched++;
							if (searched >= 50) break;
						} catch {
							// Skip inaccessible
						}
					}

					if (results.length === 0)
						return `No matches for "${args.query}" in ${searched} sessions.`;

					return `# Results: "${args.query}"\n\n${results.join("\n\n")}`;
				},
			}),

			/** Like AmpCode's read_thread */
			read_session: tool({
				description: `Read session messages.
	
Example:
read_session({ session_id: "abc123" })
read_session({ session_id: "abc123", focus: "auth" })`,
				args: {
					session_id: tool.schema.string().describe("Session ID"),
					focus: tool.schema.string().optional().describe("Filter by keyword"),
				},
				async execute(args: { session_id: string; focus?: string }) {
					const session = await client.session.get({
						path: { id: args.session_id },
					});
					if (!session.data) return `Session ${args.session_id} not found.`;

					const messages = await client.session.messages({
						path: { id: args.session_id },
					});
					const messageData = messages.data;
					if (!messageData) return `No messages in ${args.session_id}.`;

					let summary = `# ${session.data.title || "Untitled"}\n`;
					summary += `ID: ${session.data.id}\n`;
					summary += `Created: ${session.data.time?.created ? new Date(session.data.time.created).toLocaleString() : "Unknown"}\n`;
					summary += `Messages: ${messageData.length}\n\n`;

					if (args.focus) {
						const focusLower = args.focus.toLowerCase();
						const relevant = messageData.filter(
							(m: any) =>
								m.info &&
								JSON.stringify(m.info).toLowerCase().includes(focusLower),
						);
						summary += `## Matching "${args.focus}" (${relevant.length})\n\n`;
						relevant.slice(0, 5).forEach((m: any, i: number) => {
							summary += `${i + 1}. **${m.info.role}**: ${extractContent(m.info).substring(0, 200)}\n\n`;
						});
					} else {
						// Show recent user messages
						const userMessages = messageData.filter(
							(m: any) => m.info?.role === "user",
						);
						summary += "## Recent User Messages\n\n";
						for (let i = 0; i < Math.min(userMessages.length, 5); i++) {
							summary += `${i + 1}. ${extractContent(userMessages[i].info).substring(0, 200)}\n`;
						}

						// Last assistant response
						const assistantMessages = messageData.filter(
							(m: any) => m.info?.role === "assistant",
						);
						if (assistantMessages.length > 0) {
							const last = assistantMessages[assistantMessages.length - 1];
							summary += `\n## Last Response\n\n${extractContent(last.info).substring(0, 500)}\n`;
						}
					}

					return summary;
				},
			}),
		},
	};
};

function extractContent(messageInfo: any): string {
	if (!messageInfo) return "[No info]";
	if (typeof messageInfo.summary === "object" && messageInfo.summary !== null) {
		if (messageInfo.summary.title) return messageInfo.summary.title;
		if (messageInfo.summary.body) return messageInfo.summary.body;
	}
	return "[No content]";
}
