import "./globals.css";

export const metadata = {
  title: "Speaker Confidence Dashboard",
  description:
    "Real-time analytics dashboard for speech body-language confidence scoring powered by YOLO pose detection.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          <header className="app-header">
            <div className="header-inner">
              <a href="/" className="logo">
                <span className="logo-icon">🎤</span>
                <span className="logo-text">Speaker Confidence</span>
              </a>
              <span className="header-badge">YOLO Pose AI</span>
            </div>
          </header>
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
