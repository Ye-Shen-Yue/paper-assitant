import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Sparkles, RotateCcw, Loader2 } from 'lucide-react';
import { useT } from '../../hooks/useTranslation';
import { chatWithPaper, quickAction, type ChatMessage as ChatMessageType } from '../../api/chat';
import { useUIStore } from '../../store/uiStore';
import ChatMessage from './ChatMessage';
import QuickActions from './QuickActions';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Props {
  paperId: string;
  paperTitle: string;
  selectedText?: string;
  onClearSelection?: () => void;
}

export default function ChatWidget({ paperId, paperTitle, selectedText, onClearSelection }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const t = useT();
  const { language } = useUIStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  useEffect(() => {
    if (selectedText && isOpen) {
      const selectionMessage = `${t('chat.selectText')}: "${selectedText.substring(0, 100)}${selectedText.length > 100 ? '...' : ''}"`;
      setInput(selectionMessage);
      if (onClearSelection) onClearSelection();
    }
  }, [selectedText, isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Check if this is a quick action command
      const quickActions = ['summarize', 'translate', 'explain', 'critique'];
      const lowerInput = input.toLowerCase().trim();

      let response: string;

      if (quickActions.some(action => lowerInput.includes(t(`chat.${action}`).toLowerCase()))) {
        // Use quick action API
        const action = quickActions.find(a => lowerInput.includes(t(`chat.${a}`).toLowerCase())) as 'summarize' | 'translate' | 'explain' | 'critique';
        const result = await quickAction(paperId, {
          action,
          target_language: language,
        });
        response = result.response;
      } else {
        // Use chat API
        const history: ChatMessageType[] = messages.map(m => ({
          role: m.role,
          content: m.content,
        }));

        const result = await chatWithPaper(paperId, {
          message: input,
          history,
          language,
        });
        response = result.response;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = async (action: string) => {
    setIsLoading(true);

    try {
      const result = await quickAction(paperId, {
        action: action as 'summarize' | 'translate' | 'explain' | 'critique',
        target_language: language,
      });

      const actionLabel = t(`chat.${action}`);
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: `${actionLabel}`,
        timestamp: new Date(),
      };

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: result.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (error) {
      console.error('Quick action error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 hover:shadow-xl transition-all z-40"
      >
        <MessageCircle className="w-5 h-5" />
        <span className="font-medium">{t('chat.title')}</span>
        <Sparkles className="w-4 h-4 text-yellow-300" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5" />
          <span className="font-semibold">{t('chat.title')}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={clearChat}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            title={t('chat.new')}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions onAction={handleQuickAction} />

      {/* Messages */}
      <div className="flex-1 h-80 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">{t('chat.placeholder')}</p>
            <p className="text-xs mt-2 opacity-70">{paperTitle}</p>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
        {isLoading && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{t('chat.loading')}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-100 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={t('chat.placeholder')}
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
