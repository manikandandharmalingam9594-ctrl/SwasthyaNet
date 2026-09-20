import React, { useState, useEffect, useRef, useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Bot, 
  X, 
  Send, 
  Sparkles, 
  Loader2, 
  Minimize2, 
  Maximize2, 
  RotateCcw, 
  ShieldCheck, 
  Activity, 
  Package, 
  Bed, 
  AlertTriangle, 
  TrendingUp,
  ChevronDown,
  ChevronUp,
  Info,
  Compass,
  ArrowRight,
  Lock
} from 'lucide-react';
import api from '../services/api';
import { AuthContext } from '../context/AuthContext';

const DEFAULT_SUGGESTIONS = [
  "Predict Paracetamol stockout risk",
  "Open medicine inventory",
  "Forecast General ward bed occupancy",
  "Show bed occupancy",
  "Which medicines are at risk and open inventory?",
  "Go to user management",
  "Open Super Admin dashboard"
];

const ChatbotWidget = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      intent: 'UNKNOWN',
      text: `👋 **Welcome to SwasthyaNet AI Assistant!**\n\nI can assist you with both **Clinical/Operational Intelligence** and **Role-Aware Application Navigation**:\n\n📊 **Healthcare Q&A & AI Predictions:**\n- 💊 Medicine Inventory & Phase 5E LightGBM Stock-Out Predictions\n- 🛏️ Bed Occupancy & Multi-Horizon Bed Surge Forecasts (t+1, t+7, t+14)\n- 🚨 Active Operational & Clinical Alerts\n\n🧭 **Application Navigation (Role-Aware):**\n- _"Open inventory"_, _"Show bed occupancy"_, _"Go to user management"_\n- _"Which medicines are at risk and open inventory?"_\n\n🔒 *Strictly read-only & RBAC-protected.* How can I assist you?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggested_actions: DEFAULT_SUGGESTIONS
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedDataIndex, setExpandedDataIndex] = useState(null);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
      inputRef.current?.focus();
    }
  }, [messages, isOpen, isMinimized]);

  // Don't render widget if user is not authenticated
  if (!user) return null;

  // ---------------------------------------------------------------------------
  // Role-Aware Navigation Executor (Client-Side RBAC Guarded)
  // ---------------------------------------------------------------------------
  const executeNavigation = (navAction) => {
    if (!navAction || !navAction.authorized) return;

    const dest = navAction.destination;
    const role = user.role;
    const centreId = navAction.params?.centre_id || user.centre_id;
    const districtId = navAction.params?.district_id || user.district_id;
    const tab = navAction.params?.tab;
    const sectionId = navAction.params?.section_id;

    let targetPath = null;

    // 1. Super Admin Dashboard
    if (dest === 'SUPER_ADMIN_DASHBOARD') {
      if (role === 'SUPER_ADMIN') {
        targetPath = '/super-admin';
      }
    }
    // 2. District Admin Dashboard
    else if (dest === 'DISTRICT_ADMIN_DASHBOARD') {
      if (role === 'SUPER_ADMIN' || role === 'DISTRICT_ADMIN') {
        targetPath = '/district-admin';
      }
    }
    // 3. User / Staff Management
    else if (dest === 'USER_MANAGEMENT') {
      if (role === 'SUPER_ADMIN') {
        targetPath = '/super-admin';
        window.dispatchEvent(new CustomEvent('swasthyanet-tab-change', { detail: { tab: 'users' } }));
      } else if (role === 'DISTRICT_ADMIN') {
        targetPath = '/district-admin';
        window.dispatchEvent(new CustomEvent('swasthyanet-tab-change', { detail: { tab: 'staff' } }));
      }
    }
    // 4. AI Insights Tab
    else if (dest === 'AI_INSIGHTS') {
      if (role === 'SUPER_ADMIN') {
        targetPath = '/super-admin';
        window.dispatchEvent(new CustomEvent('swasthyanet-tab-change', { detail: { tab: 'ai_insights' } }));
      } else if (role === 'DISTRICT_ADMIN') {
        targetPath = '/district-admin';
        window.dispatchEvent(new CustomEvent('swasthyanet-tab-change', { detail: { tab: 'ai_insights' } }));
      } else if (role === 'PHC_STAFF') {
        targetPath = '/phc';
      } else if (role === 'CHC_STAFF') {
        targetPath = '/chc';
      }
    }
    // 5. Inventory Section / Page
    else if (dest === 'INVENTORY') {
      if (role === 'PHC_STAFF') {
        targetPath = '/phc';
      } else if (role === 'CHC_STAFF') {
        targetPath = '/chc';
      } else if (role === 'DISTRICT_ADMIN') {
        targetPath = centreId ? `/centres/${centreId}` : '/district-admin';
      } else if (role === 'SUPER_ADMIN') {
        targetPath = centreId ? `/centres/${centreId}` : '/super-admin';
      }
    }
    // 6. Beds / Bed Status Section
    else if (dest === 'BED_STATUS' || dest === 'BED_FORECAST') {
      if (role === 'PHC_STAFF') {
        targetPath = '/phc';
      } else if (role === 'CHC_STAFF') {
        targetPath = '/chc';
      } else if (role === 'DISTRICT_ADMIN') {
        targetPath = centreId ? `/centres/${centreId}` : '/district-admin';
      } else if (role === 'SUPER_ADMIN') {
        targetPath = centreId ? `/centres/${centreId}` : '/super-admin';
      }
    }
    // 7. Generic Dashboard / Home
    else if (dest === 'DASHBOARD' || dest === 'PHC_DASHBOARD' || dest === 'CHC_DASHBOARD') {
      if (role === 'SUPER_ADMIN') targetPath = '/super-admin';
      else if (role === 'DISTRICT_ADMIN') targetPath = '/district-admin';
      else if (role === 'PHC_STAFF') targetPath = '/phc';
      else if (role === 'CHC_STAFF') targetPath = '/chc';
    }
    // 8. Alerts
    else if (dest === 'ALERTS') {
      if (role === 'SUPER_ADMIN') targetPath = '/super-admin';
      else if (role === 'DISTRICT_ADMIN') targetPath = '/district-admin';
      else if (role === 'PHC_STAFF') targetPath = '/phc';
      else if (role === 'CHC_STAFF') targetPath = '/chc';
    }
    // 9. Attendance
    else if (dest === 'ATTENDANCE') {
      if (role === 'PHC_STAFF') targetPath = '/phc';
      else if (role === 'CHC_STAFF') targetPath = '/chc';
    }

    if (targetPath) {
      navigate(targetPath);
      if (tab) {
        window.dispatchEvent(new CustomEvent('swasthyanet-tab-change', { detail: { tab } }));
      }
    }
  };

  const handleSendMessage = async (textToSend = inputMessage) => {
    const query = textToSend.trim();
    if (!query || isLoading) return;

    const userMsgId = Date.now().toString();
    const userMsg = {
      id: userMsgId,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const payload = {
        message: query,
        centre_id: user.centre_id || undefined
      };

      const response = await api.post('/chatbot/chat', payload);
      const data = response.data;

      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        intent: data.intent,
        text: data.answer,
        trusted_data: data.trusted_data,
        scope: data.scope,
        navigation: data.navigation,
        suggested_actions: data.suggested_actions || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMsg]);

      // Automatically execute navigation if authorized
      if (data.navigation && data.navigation.authorized) {
        executeNavigation(data.navigation);
      }

    } catch (err) {
      console.error('Chatbot API error:', err);
      const errorDetail = err.response?.data?.detail || 'An unexpected error occurred while processing your query.';
      
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        intent: 'ERROR',
        text: `⚠️ **Error:** ${errorDetail}\n\nPlease try rephrasing your question or check your connection.`,
        suggested_actions: DEFAULT_SUGGESTIONS,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-reset',
        sender: 'bot',
        intent: 'UNKNOWN',
        text: `🧹 **Chat history cleared.**\n\nHow can I help you with healthcare intelligence or application navigation today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggested_actions: DEFAULT_SUGGESTIONS
      }
    ]);
  };

  const getIntentBadge = (intent) => {
    switch (intent) {
      case 'NAVIGATION':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800"><Compass className="h-3 w-3 mr-1" /> Navigation Action</span>;
      case 'STOCKOUT':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800"><TrendingUp className="h-3 w-3 mr-1" /> LightGBM Stock-Out</span>;
      case 'BED_FORECAST':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800"><Bed className="h-3 w-3 mr-1" /> Multi-Horizon Bed Forecast</span>;
      case 'BED_STATUS':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800"><Bed className="h-3 w-3 mr-1" /> Bed Occupancy</span>;
      case 'INVENTORY':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800"><Package className="h-3 w-3 mr-1" /> Inventory Status</span>;
      case 'ALERTS':
        return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800"><AlertTriangle className="h-3 w-3 mr-1" /> Alerts</span>;
      default:
        return null;
    }
  };

  const renderFormattedText = (rawText) => {
    const lines = rawText.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('### ')) {
        return <h4 key={idx} className="font-bold text-slate-900 text-sm mt-2 mb-1">{line.replace('### ', '')}</h4>;
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={idx} className="font-bold text-slate-800 my-0.5">{line.replace(/\*\*/g, '')}</p>;
      }
      if (line.startsWith('- ')) {
        const content = line.substring(2);
        return (
          <div key={idx} className="flex items-start my-0.5 text-xs sm:text-sm text-slate-700">
            <span className="text-indigo-500 mr-2 font-bold">•</span>
            <span dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(content) }} />
          </div>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} className="h-1.5" />;
      }
      return (
        <p key={idx} className="my-0.5 text-xs sm:text-sm text-slate-700 leading-relaxed"
           dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(line) }} />
      );
    });
  };

  const formatInlineMarkdown = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="bg-slate-100 px-1 py-0.5 rounded text-indigo-700 font-mono text-[11px]">$1</code>')
      .replace(/_([^_]+)_/g, '<em>$1</em>');
  };

  return (
    <>
      {/* Floating Action Button (FAB) Trigger */}
      {!isOpen && (
        <button
          onClick={() => { setIsOpen(true); setIsMinimized(false); }}
          className="fixed bottom-5 right-5 z-50 flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-4 py-3 rounded-full shadow-xl hover:shadow-2xl transition-all transform hover:scale-105 group focus:outline-none focus:ring-4 focus:ring-indigo-300"
          aria-label="Open SwasthyaNet AI Assistant"
        >
          <div className="relative">
            <Bot className="h-6 w-6 text-white group-hover:rotate-12 transition-transform" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <span className="font-semibold text-sm tracking-wide hidden sm:inline">AI Assistant</span>
        </button>
      )}

      {/* Floating Chatbot Window / Modal */}
      {isOpen && (
        <div 
          className={`fixed z-50 transition-all duration-300 ease-in-out shadow-2xl rounded-2xl border border-slate-200 bg-white flex flex-col overflow-hidden ${
            isMinimized
              ? 'bottom-5 right-5 w-80 h-14'
              : 'bottom-4 right-4 sm:bottom-6 sm:right-6 w-[calc(100vw-2rem)] sm:w-[440px] md:w-[480px] h-[calc(100vh-5rem)] sm:h-[620px] max-h-[700px]'
          }`}
        >
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 text-white flex items-center justify-between shrink-0 shadow-md">
            <div className="flex items-center space-x-2.5">
              <div className="bg-white/15 p-1.5 rounded-lg">
                <Bot className="h-5 w-5 text-indigo-100" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="font-bold text-sm leading-tight">SwasthyaNet AI</h3>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/20 text-indigo-100 backdrop-blur-xs">
                    {user?.role?.replace('_', ' ')}
                  </span>
                </div>
                {!isMinimized && (
                  <p className="text-[10px] text-indigo-200 flex items-center mt-0.5">
                    <ShieldCheck className="h-3 w-3 mr-1 text-emerald-300" />
                    Read-Only • RBAC Protected
                  </p>
                )}
              </div>
            </div>

            {/* Header Controls */}
            <div className="flex items-center space-x-1">
              <button
                onClick={handleClearChat}
                title="Reset conversation"
                className="p-1.5 text-indigo-200 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? "Expand" : "Minimize"}
                className="p-1.5 text-indigo-200 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Close"
                className="p-1.5 text-indigo-200 hover:text-white hover:bg-white/10 rounded-lg transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Body (Visible when not minimized) */}
          {!isMinimized && (
            <>
              {/* Messages Container */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 scrollbar-thin">
                {messages.map((msg, index) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    {/* Intent Tag */}
                    {msg.sender === 'bot' && msg.intent && msg.intent !== 'UNKNOWN' && (
                      <div className="mb-1 ml-1 flex items-center space-x-1.5">
                        {getIntentBadge(msg.intent)}
                        {msg.navigation && msg.intent !== 'NAVIGATION' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                            <Compass className="h-2.5 w-2.5 mr-1" /> Nav Attached
                          </span>
                        )}
                      </div>
                    )}

                    {/* Message Bubble */}
                    <div
                      className={`max-w-[88%] sm:max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-xs ${
                        msg.sender === 'user'
                          ? 'bg-indigo-600 text-white rounded-br-none'
                          : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                      }`}
                    >
                      {msg.sender === 'user' ? (
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      ) : (
                        <div>{renderFormattedText(msg.text)}</div>
                      )}

                      {/* Navigation Action Button Card */}
                      {msg.navigation && (
                        <div className="mt-3 pt-2.5 border-t border-slate-100">
                          {msg.navigation.authorized ? (
                            <button
                              onClick={() => executeNavigation(msg.navigation)}
                              className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-xs py-2 px-3 rounded-xl shadow-xs transition transform hover:scale-[1.01]"
                            >
                              <Compass className="h-3.5 w-3.5" />
                              <span>Go to {msg.navigation.destination.replace(/_/g, ' ').title ? msg.navigation.destination.replace(/_/g, ' ') : msg.navigation.destination}</span>
                              <ArrowRight className="h-3.5 w-3.5 ml-1" />
                            </button>
                          ) : (
                            <div className="flex items-center space-x-2 text-xs text-rose-600 bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg font-medium">
                              <Lock className="h-3.5 w-3.5 shrink-0" />
                              <span>Restricted: {msg.navigation.reason}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Raw Data Toggle (Optional Accordion for technical transparency) */}
                      {msg.trusted_data && (
                        <div className="mt-2 pt-2 border-t border-slate-100">
                          <button
                            onClick={() => setExpandedDataIndex(expandedDataIndex === index ? null : index)}
                            className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 flex items-center transition"
                          >
                            <Info className="h-3 w-3 mr-1" />
                            {expandedDataIndex === index ? 'Hide Trusted Backend Data' : 'View Trusted Backend Data'}
                            {expandedDataIndex === index ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
                          </button>
                          {expandedDataIndex === index && (
                            <div className="mt-2 p-2 bg-slate-900 text-slate-100 rounded-lg text-[10px] font-mono overflow-x-auto max-h-40">
                              <pre>{JSON.stringify(msg.trusted_data, null, 2)}</pre>
                            </div>
                          )}
                        </div>
                      )}

                      <span className={`block text-[10px] mt-1.5 ${msg.sender === 'user' ? 'text-indigo-200 text-right' : 'text-slate-400'}`}>
                        {msg.timestamp}
                      </span>
                    </div>

                    {/* Suggested Action Chips below Bot Message */}
                    {msg.sender === 'bot' && msg.suggested_actions && msg.suggested_actions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5 max-w-[90%]">
                        {msg.suggested_actions.map((sugg, sIdx) => (
                          <button
                            key={sIdx}
                            onClick={() => handleSendMessage(sugg)}
                            disabled={isLoading}
                            className="text-[11px] bg-white hover:bg-indigo-50 border border-indigo-200 text-indigo-700 font-medium px-2.5 py-1 rounded-full shadow-2xs hover:border-indigo-400 transition transform hover:scale-[1.02] disabled:opacity-50 text-left"
                          >
                            <Sparkles className="h-2.5 w-2.5 inline mr-1 text-indigo-500" />
                            {sugg}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Loading Indicator Bubble */}
                {isLoading && (
                  <div className="flex items-center space-x-2 bg-white border border-slate-200 px-4 py-2.5 rounded-2xl rounded-bl-none w-fit shadow-xs animate-pulse">
                    <Loader2 className="h-4 w-4 text-indigo-600 animate-spin" />
                    <span className="text-xs font-medium text-slate-500">Processing query & validating navigation...</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Footer */}
              <div className="p-3 bg-white border-t border-slate-200 shrink-0">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center space-x-2"
                >
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder="Ask Q&A or navigation: 'Open inventory', 'Which medicines at risk?'..."
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition disabled:opacity-60"
                  />
                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || isLoading}
                    className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white p-2 sm:px-3.5 sm:py-2 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center transition shadow-xs disabled:cursor-not-allowed shrink-0"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Send className="h-4 w-4 sm:mr-1.5" />
                        <span className="hidden sm:inline">Send</span>
                      </>
                    )}
                  </button>
                </form>
                <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400 px-1">
                  <span>Press <kbd className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">Enter</kbd> to send</span>
                  <span>Role-aware navigation</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
};

export default ChatbotWidget;
