import { useMemo } from "react";
import { Message } from "@langchain/langgraph-sdk";

export type ViewType = "home" | "policy_qa" | "claims" | "coverage_upgrade" | "damage_assessment" | "dashboard";

/**
 * Scans the message stream for the most recent `set_active_view` tool result
 * and returns the current active view. Defaults to "home" if no tool call found.
 *
 * This is derived state — when loading a thread from history the view is
 * automatically correct because we scan all past messages.
 */
export function useActiveView(messages: Message[]): ViewType {
  return useMemo(() => {
    // Walk messages in reverse to find the most recent set_active_view tool result
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      if (msg.type === "tool" && (msg as any).name === "set_active_view") {
        try {
          const content =
            typeof msg.content === "string"
              ? JSON.parse(msg.content)
              : msg.content;
          if (content?.active_view) {
            return content.active_view as ViewType;
          }
        } catch {
          // malformed JSON, continue searching
        }
      }
    }
    return "home";
  }, [messages]);
}
