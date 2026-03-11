"use client";

import { ReactNode, useRef } from "react";
import { useStreamContext } from "@/providers/Stream";
import { Checkpoint } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "@/components/thread/messages/ai";
import { HumanMessage } from "@/components/thread/messages/human";
import { DO_NOT_RENDER_ID_PREFIX } from "@/lib/ensure-tool-responses";
import { VOICE_NAV_PREFIX } from "./VoiceNav";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import { Button } from "@/components/ui/button";
import { ArrowDown } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Returns true if the message is a voice-navigation command that should
 * be hidden from the chat display. Checks human messages whose text
 * content starts with the [VOICE_NAV] prefix.
 */
function isVoiceNavMessage(message: { type: string; content: unknown }): boolean {
  if (message.type !== "human") return false;
  const content = message.content;
  if (typeof content === "string") return content.startsWith(VOICE_NAV_PREFIX);
  if (Array.isArray(content)) {
    const firstText = content.find(
      (b: Record<string, unknown>) => b.type === "text",
    ) as { text?: string } | undefined;
    return firstText?.text?.startsWith(VOICE_NAV_PREFIX) ?? false;
  }
  return false;
}

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  return (
    <div
      ref={context.scrollRef}
      style={{ width: "100%", height: "100%" }}
      className={props.className}
    >
      <div ref={context.contentRef} className={props.contentClassName}>
        {props.content}
      </div>
      {props.footer}
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();
  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="h-4 w-4" />
      <span>Scroll to bottom</span>
    </Button>
  );
}

interface ChatPanelProps {
  /** Optional footer element (e.g., input bar) rendered below messages */
  footer?: ReactNode;
  /** Extra classes for the outer wrapper */
  className?: string;
  /** Extra classes for the scroll content area */
  contentClassName?: string;
}

/**
 * Shared scrollable message list component.
 * Renders all messages from the stream and sticks to the bottom.
 */
export function ChatPanel({ footer, className, contentClassName }: ChatPanelProps) {
  const stream = useStreamContext();
  const messages = stream.messages;
  const isLoading = stream.isLoading;

  const prevMessageLength = useRef(0);
  const [firstTokenReceived, setFirstTokenReceived] = React.useState(false);

  React.useEffect(() => {
    if (
      messages.length !== prevMessageLength.current &&
      messages?.length &&
      messages[messages.length - 1].type === "ai"
    ) {
      setFirstTokenReceived(true);
    }
    prevMessageLength.current = messages.length;
  }, [messages]);

  const hasNoAIOrToolMessages = !messages.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  const handleRegenerate = (parentCheckpoint: Checkpoint | null | undefined) => {
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
    });
  };

  return (
    <StickToBottom className={cn("relative flex-1 overflow-hidden", className)}>
      <StickyToBottomContent
        className="absolute inset-0 overflow-y-scroll px-4 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-track]:bg-transparent"
        contentClassName={cn(
          "pt-8 pb-16 max-w-3xl mx-auto flex flex-col gap-4 w-full",
          contentClassName,
        )}
        content={
          <>
            {messages
              .filter(
                (m) =>
                  !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX) &&
                  !isVoiceNavMessage(m),
              )
              .map((message, index) =>
                message.type === "human" ? (
                  <HumanMessage
                    key={message.id || `${message.type}-${index}`}
                    message={message}
                    isLoading={isLoading}
                  />
                ) : (
                  <AssistantMessage
                    key={message.id || `${message.type}-${index}`}
                    message={message}
                    isLoading={isLoading}
                    handleRegenerate={handleRegenerate}
                  />
                ),
              )}
            {hasNoAIOrToolMessages && !!stream.interrupt && (
              <AssistantMessage
                key="interrupt-msg"
                message={undefined}
                isLoading={isLoading}
                handleRegenerate={handleRegenerate}
              />
            )}
            {isLoading && !firstTokenReceived && <AssistantMessageLoading />}
          </>
        }
        footer={
          <div className="sticky bottom-0 flex flex-col items-center gap-4">
            <ScrollToBottom className="animate-in fade-in-0 zoom-in-95 absolute bottom-full left-1/2 mb-4 -translate-x-1/2" />
            {footer}
          </div>
        }
      />
    </StickToBottom>
  );
}

// Need React import for the hooks
import React from "react";
