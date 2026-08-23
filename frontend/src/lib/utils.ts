import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), "MMM d, yyyy");
}

export function getFileTypeIcon(fileType: string): string {
  const icons: Record<string, string> = {
    pdf: "📄",
    docx: "📝",
    pptx: "📊",
    xlsx: "📈",
    markdown: "📋",
    txt: "📃",
    csv: "📊",
    html: "🌐",
    ipynb: "🔬",
    code: "💻",
  };
  return icons[fileType] || "📄";
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    completed: "text-emerald-500",
    processing: "text-blue-500",
    pending: "text-amber-500",
    failed: "text-red-500",
    synced: "text-emerald-500",
    syncing: "text-blue-500",
  };
  return colors[status] || "text-muted-foreground";
}

export function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    super_admin: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    workspace_admin: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    manager: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    employee: "bg-green-500/10 text-green-400 border-green-500/20",
    guest: "bg-gray-500/10 text-gray-400 border-gray-500/20",
  };
  return colors[role] || "bg-gray-500/10 text-gray-400";
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + "...";
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export const SUGGESTED_PROMPTS = [
  "What is the employee leave policy?",
  "Summarize the backend architecture",
  "How does authentication work in our system?",
  "What are the coding standards?",
  "Explain the CI/CD pipeline",
  "What are the latest release notes?",
  "How do I set up Docker locally?",
  "What is the database design for the users table?",
];
