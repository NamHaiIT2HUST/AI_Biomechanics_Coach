import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Biomechanics Coach | Phân tích squat",
  description: "Phân tích video squat và xem lại từng rep.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="vi"><body>{children}</body></html>;
}
