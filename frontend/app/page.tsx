"use client";

import { FormEvent, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";

import ReactMarkdown from "react-markdown";

import remarkGfm from "remark-gfm";

type Message = {

  role: "user" | "assistant";

  content: string;

};

type Source = {

  filename: string;

  path: string;

  title: string;

  chunk: number;

  distance: number;

};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
};

// Recent chats are kept in this browser's localStorage.
const STORAGE_KEY = "kloc-ai-conversations";

const MAX_CONVERSATIONS = 50;

const storageListeners = new Set<() => void>();

const subscribeToStorage = (listener: () => void) => {
  storageListeners.add(listener);
  window.addEventListener("storage", listener);

  return () => {
    storageListeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
};

const readStoredConversations = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? "[]";
  } catch {
    return "[]";
  }
};

const parseConversations = (raw: string): Conversation[] => {
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const writeConversations = (conversations: Conversation[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch {
    // Storage full or blocked: chats just won't persist.
  }

  storageListeners.forEach((listener) => listener());
};

const saveConversation = (id: string, messages: Message[]) => {
  const stored = parseConversations(readStoredConversations());
  const existing = stored.find((conversation) => conversation.id === id);

  writeConversations(
    [
      {
        id,
        title: existing?.title ?? titleFor(messages),
        messages,
        updatedAt: Date.now(),
      },
      ...stored.filter((conversation) => conversation.id !== id),
    ].slice(0, MAX_CONVERSATIONS)
  );
};

const titleFor = (messages: Message[]) => {
  const first = messages.find((message) => message.role === "user")?.content ?? "New chat";
  return first.length > 40 ? `${first.slice(0, 40).trimEnd()}…` : first;
};

type StreamMetadata = {
  retrieval_query?: string;
  sources?: Source[];
};

const API_URL = process.env.NEXT_API_URL ?? "http://127.0.0.1:8000";

const suggestedQuestions = [

  "What does KLOCOM do?",

  "What services does KLOC provide?",

  "What does KLOCERS do?",

  "What AI capabilities does KLOC offer?",

];

export default function Home() {

  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);

  const [sources, setSources] = useState<Source[]>([]);

  const [retrievalQuery, setRetrievalQuery] = useState("");

  const storedConversations = useSyncExternalStore(
    subscribeToStorage,
    readStoredConversations,
    () => "[]"
  );

  const conversations = useMemo(
    () => parseConversations(storedConversations),
    [storedConversations]
  );

  const [activeId, setActiveId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {

    messagesEndRef.current?.scrollIntoView({

      behavior: "smooth",

    });

  }, [messages, loading]);

  const sendMessage = async (event?: FormEvent) => {
    event?.preventDefault();

    const question = input.trim();

    if (!question || loading) {
      return;
    }

    // Capture previous conversation history before adding this question.
    const history = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    const userMessage: Message = {
      role: "user",
      content: question,
    };

    // The user message is at the previous message count; the assistant
    // placeholder is immediately after it.
    const assistantMessageIndex = messages.length + 1;

    setMessages((previous) => [
      ...previous,
      userMessage,
      { role: "assistant", content: "" },
    ]);

    const conversationId = activeId ?? crypto.randomUUID();
    setActiveId(conversationId);

    let finalAnswer = "";

    setInput("");
    setLoading(true);
    setSources([]);
    setRetrievalQuery("");

    let streamedAnswer = "";
    let receivedDone = false;

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ question, history }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("text/event-stream")) {
        throw new Error("The server did not return a streaming response.");
      }

      if (!response.body) {
        throw new Error("The response stream is unavailable.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const processFrame = (frame: string) => {
        const lines = frame.split(/\r?\n/);
        const eventLine = lines.find((line) => line.startsWith("event:"));
        const eventType = eventLine?.slice("event:".length).trim();
        const data = lines
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice("data:".length).trimStart())
          .join("\n");

        if (!eventType || !data) {
          return;
        }

        const payload = JSON.parse(data);

        if (eventType === "metadata") {
          const metadata = payload as StreamMetadata;
          setSources(metadata.sources ?? []);
          setRetrievalQuery(metadata.retrieval_query ?? "");
        } else if (eventType === "token") {
          const text = typeof payload.text === "string" ? payload.text : "";
          streamedAnswer += text;
          const currentAnswer = streamedAnswer;

          setMessages((previous) =>
            previous.map((message, index) =>
              index === assistantMessageIndex
                ? { ...message, content: currentAnswer }
                : message
            )
          );
        } else if (eventType === "done") {
          receivedDone = true;
        } else if (eventType === "error") {
          throw new Error(
            typeof payload.message === "string"
              ? payload.message
              : "The response stream was interrupted."
          );
        }
      };

      // Network chunks may split an SSE event or contain multiple events.
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() ?? "";

        for (const frame of frames) {
          if (frame.trim()) {
            processFrame(frame);
          }
        }
      }

      buffer += decoder.decode();
      if (buffer.trim()) {
        processFrame(buffer);
      }

      if (!receivedDone) {
        throw new Error("The response stream ended unexpectedly.");
      }

      finalAnswer = streamedAnswer;
    } catch (error) {
      console.error("Chat streaming error:", error);

      const errorMessage = streamedAnswer
        ? `${streamedAnswer}\n\nThe response was interrupted. Please try again.`
        : "Sorry, I couldn't process your request right now. Please try again.";

      finalAnswer = errorMessage;

      setMessages((previous) => {
        const updated = [...previous];
        const assistantMessage = updated[assistantMessageIndex];

        if (assistantMessage?.role === "assistant") {
          updated[assistantMessageIndex] = {
            ...assistantMessage,
            content: errorMessage,
          };
        } else {
          updated.push({ role: "assistant", content: errorMessage });
        }

        return updated;
      });
    } finally {
      setLoading(false);

      saveConversation(conversationId, [
        ...messages,
        userMessage,
        { role: "assistant", content: finalAnswer },
      ]);
    }
  };

  const handleSuggestedQuestion = (question: string) => {

    setInput(question);

  };

  const startNewChat = () => {

    setMessages([]);

    setActiveId(null);

    setInput("");

    setSources([]);

    setRetrievalQuery("");

    setLoading(false);

  };

  const openConversation = (conversation: Conversation) => {
    if (loading) {
      return;
    }

    setMessages(conversation.messages);
    setActiveId(conversation.id);
    setInput("");
    setSources([]);
    setRetrievalQuery("");
  };

  const deleteConversation = (id: string) => {
    writeConversations(
      conversations.filter((conversation) => conversation.id !== id)
    );

    if (id === activeId) {
      startNewChat();
    }
  };

  return (

    <main

      className="min-h-screen"

      style={{

        background:

          "linear-gradient(135deg, #103B39 0%, #103B39 55%, #DDFAC7 180%)",

        color: "#DDFAC7",

      }}

    >

      <div className="flex min-h-screen">

        {/* SIDEBAR */}

        <aside

          className="hidden w-72 shrink-0 border-r p-5 md:flex md:flex-col"

          style={{

            borderColor: "rgba(221, 250, 199, 0.15)",

            background:

              "linear-gradient(180deg, #103B39 0%, rgba(16,59,57,0.96) 100%)",

          }}

        >

          {/* LOGO */}

          <div className="mb-8">

            <div className="text-2xl font-bold tracking-tight">

              KLOC

            </div>

            <div

              className="mt-1 text-xs"

              style={{

                color: "rgba(221, 250, 199, 0.65)",

              }}

            >

              Intelligent Business Assistant

            </div>

          </div>

          {/* NEW CHAT */}

          <button

            onClick={startNewChat}

            className="mb-8 rounded-xl px-4 py-3 text-sm font-semibold transition-all hover:scale-[1.02]"

            style={{

              color: "#103B39",

              background:

                "linear-gradient(135deg, #DDFAC7 0%, #103B39 160%)",

              boxShadow:

                "0 8px 30px rgba(221, 250, 199, 0.15)",

            }}

          >

            + New Chat

          </button>

          {/* RECENT */}

          <div>

            <div

              className="mb-3 text-xs font-semibold uppercase tracking-wider"

              style={{

                color: "rgba(221, 250, 199, 0.5)",

              }}

            >

              Recent

            </div>

            {conversations.length > 0 ? (

              <ul className="space-y-1 overflow-y-auto" style={{ maxHeight: "calc(100vh - 300px)" }}>

                {conversations.map((conversation) => (

                  <li key={conversation.id} className="group flex items-center rounded-lg"
                    style={{
                      background:
                        conversation.id === activeId ? "rgba(221, 250, 199, 0.12)" : "transparent",
                    }}
                  >

                    <button
                      type="button"
                      onClick={() => openConversation(conversation)}
                      disabled={loading}
                      title={conversation.title}
                      className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm transition-colors hover:opacity-100 disabled:cursor-not-allowed"
                      style={{
                        color: "#DDFAC7",
                        opacity: conversation.id === activeId ? 1 : 0.75,
                      }}
                    >
                      {conversation.title}
                    </button>

                    <button
                      type="button"
                      onClick={() => deleteConversation(conversation.id)}
                      disabled={loading}
                      aria-label={`Delete chat: ${conversation.title}`}
                      className="px-2 py-2 text-sm opacity-0 transition-opacity group-hover:opacity-60 hover:!opacity-100 focus:opacity-100 disabled:hidden"
                      style={{ color: "#DDFAC7" }}
                    >
                      ×
                    </button>

                  </li>

                ))}

              </ul>

            ) : (

              <div

                className="text-sm"

                style={{

                  color:

                    "rgba(221, 250, 199, 0.4)",

                }}

              >

                No recent chats

              </div>

            )}

          </div>

          {/* FOOTER */}

          <div className="mt-auto">

            <div

              className="text-xs leading-5"

              style={{

                color:

                  "rgba(221, 250, 199, 0.4)",

              }}

            >

              KLOC AI

              <br />

              Knowledge-powered assistant

            </div>

          </div>

        </aside>

        {/* MAIN */}

        <section className="flex min-w-0 flex-1 flex-col">

          {/* MOBILE HEADER */}

          <header className="flex items-center justify-between border-b p-4 md:hidden"

            style={{

              borderColor:

                "rgba(221, 250, 199, 0.15)",

            }}

          >

            <div>

              <div className="font-bold">

                KLOC

              </div>

              <div

                className="text-xs"

                style={{

                  color:

                    "rgba(221, 250, 199, 0.55)",

                }}

              >

                KLOC AI

              </div>

            </div>

            <button

              onClick={startNewChat}

              className="rounded-lg px-3 py-2 text-sm font-semibold"

              style={{

                background: "#DDFAC7",

                color: "#103B39",

              }}

            >

              New Chat

            </button>

          </header>

          {/* CHAT AREA */}

          <div className="flex-1 overflow-y-auto">

            {messages.length === 0 ? (

              <div className="mx-auto flex min-h-[calc(100vh-220px)] max-w-4xl flex-col items-center justify-center px-5 text-center">

                <div

                  className="mb-5 rounded-2xl px-5 py-3 text-sm font-medium"

                  style={{

                    background:

                      "linear-gradient(135deg, rgba(221,250,199,0.12), rgba(221,250,199,0.04))",

                    border:

                      "1px solid rgba(221,250,199,0.12)",

                  }}

                >

                  KLOC AI

                </div>

                <h1 className="text-4xl font-bold tracking-tight md:text-6xl">

                  How can I help you?

                </h1>

                <p

                  className="mt-5 max-w-2xl text-sm leading-6 md:text-base"

                  style={{

                    color:

                      "rgba(221, 250, 199, 0.6)",

                  }}

                >

                  Ask me about KLOC Technologies,

                  our services, divisions, projects,

                  AI capabilities, and more.

                </p>

                {/* SUGGESTIONS */}

                <div className="mt-8 flex flex-wrap justify-center gap-3">

                  {suggestedQuestions.map(

                    (question) => (

                      <button

                        key={question}

                        onClick={() =>

                          handleSuggestedQuestion(

                            question

                          )

                        }

                        className="rounded-full border px-4 py-2 text-sm transition-all hover:scale-[1.02]"

                        style={{

                          borderColor:

                            "rgba(221,250,199,0.2)",

                          background:

                            "rgba(221,250,199,0.05)",

                          color: "#DDFAC7",

                        }}

                      >

                        {question}

                      </button>

                    )

                  )}

                </div>

              </div>

            ) : (

              <div className="mx-auto max-w-4xl space-y-6 px-5 py-8">

                {messages.map(

                  (message, index) => message.role === "assistant" && message.content === "" ? null : (

                    <div

                      key={`${message.role}-${index}`}

                      className={`flex ${

                        message.role === "user"

                          ? "justify-end"

                          : "justify-start"

                      }`}

                    >

                      <div

                        className="max-w-[85%] rounded-2xl px-5 py-4"

                        style={

                          message.role === "user"

                            ? {

                                background:

                                  "linear-gradient(135deg, #DDFAC7 0%, rgba(221,250,199,0.75) 100%)",

                                color: "#103B39",

                              }

                            : {

                                background:

                                  "linear-gradient(135deg, rgba(221,250,199,0.08), rgba(221,250,199,0.03))",

                                border:

                                  "1px solid rgba(221,250,199,0.1)",

                                color: "#DDFAC7",

                              }

                        }

                      >

                        {message.role ===

                        "assistant" ? (

                          <div className="prose prose-invert max-w-none text-sm leading-7">

                            <ReactMarkdown

                              remarkPlugins={[

                                remarkGfm,

                              ]}

                            >

                              {message.content}

                            </ReactMarkdown>

                          </div>

                        ) : (

                          <div className="text-sm leading-6">

                            {message.content}

                          </div>

                        )}

                      </div>

                    </div>

                  )

                )}

                {/* LOADING */}

                {loading && messages[messages.length - 1]?.content === "" && (

                  <div className="flex justify-start">

                    <div

                      className="rounded-2xl px-5 py-4"

                      style={{

                        background:

                          "rgba(221,250,199,0.06)",

                        border:

                          "1px solid rgba(221,250,199,0.1)",

                      }}

                    >

                      <div className="flex items-center gap-2">

                        <span

                          className="h-2 w-2 animate-bounce rounded-full"

                          style={{

                            background: "#DDFAC7",

                          }}

                        />

                        <span

                          className="h-2 w-2 animate-bounce rounded-full [animation-delay:150ms]"

                          style={{

                            background: "#DDFAC7",

                          }}

                        />

                        <span

                          className="h-2 w-2 animate-bounce rounded-full [animation-delay:300ms]"

                          style={{

                            background: "#DDFAC7",

                          }}

                        />

                      </div>

                    </div>

                  </div>

                )}

                <div ref={messagesEndRef} />

              </div>

            )}

          </div>

          {/* SOURCES */}

          {sources.length > 0 && (

            <div className="mx-auto w-full max-w-4xl px-5 pb-3">

              <details

                className="rounded-xl border p-4"

                style={{

                  borderColor:

                    "rgba(221,250,199,0.1)",

                  background:

                    "rgba(221,250,199,0.04)",

                }}

              >

                <summary

                  className="cursor-pointer text-sm font-semibold"

                >

                  Sources ({sources.length})

                </summary>

                <div className="mt-4 space-y-3">

                  {sources.map(

                    (source, index) => (

                      <div

                        key={`${source.path}-${source.chunk}-${index}`}

                        className="rounded-lg p-3"

                        style={{

                          background:

                            "rgba(221,250,199,0.04)",

                        }}

                      >

                        <div className="text-sm font-semibold">

                          {source.filename}

                        </div>

                        <div

                          className="mt-1 text-xs"

                          style={{

                            color:

                              "rgba(221,250,199,0.55)",

                          }}

                        >

                          {source.title}

                        </div>

                        <div

                          className="mt-2 text-xs"

                          style={{

                            color:

                              "rgba(221,250,199,0.4)",

                          }}

                        >

                          Distance:{" "}

                          {source.distance.toFixed(

                            4

                          )}

                        </div>

                      </div>

                    )

                  )}

                </div>

                {retrievalQuery && (

                  <div

                    className="mt-4 rounded-lg p-3 text-xs"

                    style={{

                      background:

                        "rgba(221,250,199,0.04)",

                    }}

                  >

                    <div className="font-semibold">

                      Retrieval Query

                    </div>

                    <div

                      className="mt-1"

                      style={{

                        color:

                          "rgba(221,250,199,0.55)",

                      }}

                    >

                      {retrievalQuery}

                    </div>

                  </div>

                )}

              </details>

            </div>

          )}

          {/* INPUT AREA */}

          <div className="border-t p-4"

            style={{

              borderColor:

                "rgba(221,250,199,0.12)",

              background:

                "rgba(16,59,57,0.75)",

            }}

          >

            <form

              onSubmit={sendMessage}

              className="mx-auto max-w-4xl"

            >

              <div

                className="rounded-2xl p-[1px]"

                style={{

                  background:

                    "linear-gradient(90deg, #DDFAC7, #103B39, #DDFAC7)",

                }}

              >

                <div

                  className="flex items-end gap-3 rounded-2xl p-3"

                  style={{

                    background: "#103B39",

                  }}

                >

                  <textarea

                    value={input}

                    onChange={(event) =>

                      setInput(

                        event.target.value

                      )

                    }

                    onKeyDown={(event) => {

                      if (

                        event.key === "Enter" &&

                        !event.shiftKey

                      ) {

                        event.preventDefault();

                        sendMessage();

                      }

                    }}

                    placeholder="Ask KLOC AI anything..."

                    rows={1}

                    disabled={loading}

                    className="max-h-32 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:opacity-40"

                    style={{

                      color: "#DDFAC7",

                    }}

                  />

                  <button

                    type="submit"

                    disabled={

                      loading ||

                      !input.trim()

                    }

                    className="rounded-xl px-5 py-3 text-sm font-bold transition-all hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-40"

                    style={{

                      background:

                        "linear-gradient(135deg, #DDFAC7 0%, rgba(221,250,199,0.75) 100%)",

                      color: "#103B39",

                    }}

                  >

                    Send

                  </button>

                </div>

              </div>

              <div

                className="mt-3 text-center text-xs"

                style={{

                  color:

                    "rgba(221,250,199,0.35)",

                }}

              >

                KLOC AI can make mistakes. Verify

                important information.

              </div>

            </form>

          </div>

        </section>

      </div>

    </main>

  );

}
