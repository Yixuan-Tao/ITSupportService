"use client";

import { useState, useEffect } from "react";
import { ticketApi, Ticket } from "@/api/client";
import { RefreshCw, ExternalLink, Clock, AlertCircle, CheckCircle } from "lucide-react";

interface TicketListProps {
  className?: string;
}

const statusConfig: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
  open: { bg: "bg-amber-100", text: "text-amber-700", icon: <Clock className="w-3 h-3" /> },
  in_progress: { bg: "bg-blue-100", text: "text-blue-700", icon: <RefreshCw className="w-3 h-3" /> },
  resolved: { bg: "bg-green-100", text: "text-green-700", icon: <CheckCircle className="w-3 h-3" /> },
  closed: { bg: "bg-slate-100", text: "text-slate-600", icon: <CheckCircle className="w-3 h-3" /> },
};

const priorityConfig: Record<string, { bg: string; text: string }> = {
  low: { bg: "bg-slate-100", text: "text-slate-600" },
  medium: { bg: "bg-blue-100", text: "text-blue-700" },
  high: { bg: "bg-orange-100", text: "text-orange-700" },
  critical: { bg: "bg-red-100", text: "text-red-700" },
};

export default function TicketList({ className = "" }: TicketListProps) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await ticketApi.sync();
      const data = await ticketApi.list();
      setTickets(data || []);
    } catch (err) {
      console.error("获取工单列表失败:", err);
      setError("加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden ${className}`}>
      <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
              <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800">我的工单</h2>
              <p className="text-xs text-slate-500">共 {tickets.length} 个工单</p>
            </div>
          </div>
          <button
            onClick={fetchTickets}
            disabled={isLoading}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="p-6">
        {isLoading && tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <RefreshCw className="w-8 h-8 text-slate-300 animate-spin mb-3" />
            <p className="text-sm text-slate-400">加载中...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="w-8 h-8 text-red-400 mb-3" />
            <p className="text-sm text-red-500">{error}</p>
            <button onClick={fetchTickets} className="mt-2 text-xs text-blue-500 hover:underline cursor-pointer">
              重试
            </button>
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-sm text-slate-500 mb-1">暂无工单</p>
            <p className="text-xs text-slate-400">提交问题后会自动创建工单</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tickets.map((ticket) => {
              const status = statusConfig[ticket.status] || statusConfig.open;
              const priority = priorityConfig[ticket.priority] || priorityConfig.medium;

              return (
                <div
                  key={ticket.id}
                  className="p-4 bg-slate-50 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-medium text-slate-800 truncate">{ticket.title}</h3>
                        {ticket.jira_id && (
                          <a
                            href={`${process.env.NEXT_PUBLIC_JIRA_URL || "https://tommytao0415.atlassian.net"}/browse/${ticket.jira_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 hover:bg-slate-200 rounded transition-colors"
                          >
                            <ExternalLink className="w-3 h-3 text-slate-400" />
                          </a>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 line-clamp-1 mb-2">{ticket.description}</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${status.bg} ${status.text}`}>
                          {status.icon}
                          {ticket.status}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${priority.bg} ${priority.text}`}>
                          {ticket.priority}
                        </span>
                        <span className="text-xs text-slate-400">{ticket.category}</span>
                      </div>
                    </div>
                    <span className="text-xs text-slate-400 whitespace-nowrap">{formatDate(ticket.created_at)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
