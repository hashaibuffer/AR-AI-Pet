import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 空间伙伴 · AgentOS × StackChan × XREAL",
  description:
    "GOAI 2026 AI+眼镜项目演示：私人AgentOS、StackChan实体化身与XREAL空间世界。",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
