import { useState, useRef, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { 
  Send, ArrowLeft, Sparkles, Menu, X, Plus, 
  MessageSquare, Loader2 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBoyfriend } from "@/hooks/useBoyfriends";
import { useChatSessions, useSendMessage } from "@/hooks/useChat";
import type { ChatMessage } from "@/types";

// Typing indicator component
function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center gap-3 p-4"
    >
      <Avatar className="w-8 h-8">
        <AvatarFallback className="bg-linear-to-br from-primary to-accent text-xs">
          ✨
        </AvatarFallback>
      </Avatar>
      <div className="glass px-4 py-3 rounded-2xl rounded-tl-none">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-primary rounded-full"
              animate={{ y: [0, -5, 0] }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.15,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

// Message bubble component
function MessageBubble({ message, isUser }: { message: ChatMessage; isUser: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex items-end gap-2 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {!isUser && (
        <Avatar className="w-8 h-8 shrink-0">
          <AvatarFallback className="bg-linear-to-br from-primary to-accent text-xs">
            ✨
          </AvatarFallback>
        </Avatar>
      )}
      
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl ${
          isUser
            ? "bg-linear-to-r from-primary to-accent text-white rounded-br-none"
            : "glass rounded-tl-none"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
      
      {isUser && (
        <Avatar className="w-8 h-8 shrink-0">
          <AvatarFallback className="bg-secondary text-xs">You</AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
}

// Helper function to deduplicate messages
const deduplicateMessages = (sessionHistory: ChatMessage[], optimisticMessages: ChatMessage[]): ChatMessage[] => {
  // Create a set of unique message signatures from session history
  const historySignatures = new Set(
    sessionHistory.map(msg => `${msg.role}:${msg.content}:${msg.timestamp || ''}`)
  );
  
  // Filter out optimistic messages that are already in session history
  const uniqueOptimisticMessages = optimisticMessages.filter(msg => {
    const signature = `${msg.role}:${msg.content}:${msg.timestamp || ''}`;
    return !historySignatures.has(signature);
  });
  
  return [...sessionHistory, ...uniqueOptimisticMessages];
};

export default function Chat() {
  const { boyfriendId } = useParams<{ boyfriendId: string }>();
  const navigate = useNavigate();
  
  const { data: boyfriend, isLoading: loadingBoyfriend } = useBoyfriend(boyfriendId!);
  const { data: sessions } = useChatSessions(boyfriendId);
  const sendMessage = useSendMessage();
  
  const [message, setMessage] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get current session's messages with deduplication
  const currentSession = sessions?.find(s => s.id === currentSessionId);
  const displayMessages = currentSessionId 
    ? deduplicateMessages(currentSession?.history || [], localMessages)
    : localMessages;

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    // The ref now points directly to the viewport element
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [displayMessages, isTyping, scrollToBottom]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle send message
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !boyfriendId || sendMessage.isPending) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    // Optimistic UI - show user message immediately
    setLocalMessages(prev => [...prev, userMessage]);
    setMessage("");
    setIsTyping(true);

    try {
      const response = await sendMessage.mutateAsync({
        boyfriend_id: boyfriendId,
        message: userMessage.content,
        session_id: currentSessionId || undefined,
      });

      // Update session ID if new
      if (!currentSessionId) {
        setCurrentSessionId(response.session_id);
      }

      // Add AI response
      const aiMessage: ChatMessage = {
        role: "assistant",
        content: response.ai_response,
        timestamp: new Date().toISOString(),
      };
      
      setLocalMessages(prev => [...prev, aiMessage]);
      
      // Note: Messages will be automatically deduped when sessions refetch
      // The deduplicateMessages function will prevent duplicates
    } catch (error) {
      // Remove optimistic message on error
      setLocalMessages(prev => prev.filter(m => m !== userMessage));
    } finally {
      setIsTyping(false);
    }
  };

  // Start new chat
  const handleNewChat = () => {
    setCurrentSessionId(null);
    setLocalMessages([]);
    setShowSidebar(false);
    inputRef.current?.focus();
  };

  // Select existing session
  const handleSelectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setLocalMessages([]);
    setShowSidebar(false);
  };

  if (loadingBoyfriend) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!boyfriend) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Soulmate not found</p>
        <Button onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="shrink-0 glass border-b border-border/50 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate("/dashboard")}
              className="md:hidden"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <Link to="/dashboard" className="hidden md:block">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="w-5 h-5" />
              </Button>
            </Link>
            
            <Avatar className="w-10 h-10">
              <AvatarFallback className="bg-linear-to-br from-primary to-accent">
                ✨
              </AvatarFallback>
            </Avatar>
            
            <div>
              <h1 className="font-semibold">{boyfriend.name}</h1>
              <p className="text-xs text-muted-foreground">Online</p>
            </div>
          </div>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowSidebar(!showSidebar)}
          >
            {showSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar */}
        <AnimatePresence>
          {showSidebar && (
            <>
              {/* Backdrop for mobile */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/50 z-40 md:hidden"
                onClick={() => setShowSidebar(false)}
              />
              
              {/* Sidebar panel */}
              <motion.aside
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className="absolute right-0 top-0 bottom-0 w-72 glass border-l border-border/50 z-50 flex flex-col"
              >
                <div className="p-4 border-b border-border/50 flex items-center justify-between">
                  <h2 className="font-semibold">Chat History</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleNewChat}
                    className="gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    New
                  </Button>
                </div>
                
                <ScrollArea className="flex-1">
                  <div className="p-2 space-y-1">
                    {sessions?.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => handleSelectSession(session.id)}
                        className={`w-full text-left p-3 rounded-lg transition-colors ${
                          currentSessionId === session.id
                            ? "bg-primary/20 text-primary"
                            : "hover:bg-secondary/50"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 shrink-0" />
                          <span className="text-sm truncate">
                            {session.title || "New Chat"}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 truncate">
                          {session.history.length} messages
                        </p>
                      </button>
                    ))}
                    
                    {(!sessions || sessions.length === 0) && (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No chat history yet
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Messages Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ScrollArea className="flex-1" ref={scrollRef}>
            <div className="p-4 space-y-4 min-h-full">
              {displayMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full py-20 text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", damping: 15 }}
                    className="w-20 h-20 rounded-full bg-linear-to-br from-primary to-accent flex items-center justify-center mb-4"
                  >
                    <Sparkles className="w-10 h-10 text-white" />
                  </motion.div>
                  <h3 className="text-lg font-semibold mb-2">
                    Start chatting with {boyfriend.name}
                  </h3>
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Your cosmic companion is ready to connect. Send a message to begin your journey together.
                  </p>
                </div>
              ) : (
                displayMessages.map((msg, index) => (
                  <MessageBubble
                    key={`${msg.timestamp}-${index}`}
                    message={msg}
                    isUser={msg.role === "user"}
                  />
                ))
              )}
              
              <AnimatePresence>
                {isTyping && <TypingIndicator />}
              </AnimatePresence>
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="shrink-0 p-4 glass border-t border-border/50">
            <form onSubmit={handleSend} className="flex gap-2">
              <Input
                ref={inputRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 bg-input/50 border-border/50"
                disabled={sendMessage.isPending}
              />
              <Button
                type="submit"
                size="icon"
                className="bg-linear-to-r from-primary to-accent hover:opacity-90"
                disabled={!message.trim() || sendMessage.isPending}
              >
                {sendMessage.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
