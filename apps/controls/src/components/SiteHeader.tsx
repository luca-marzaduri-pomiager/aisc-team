export default function SiteHeader() {
  // Neither static files in public/ nor raw <a href> links are prefixed with
  // the configured basePath the way Next's own /_next assets and <Link>
  // navigations are, so build them explicitly. Read at render time on the
  // server (same runtime NEXT_BASE_PATH next.config uses).
  const basePath = process.env.NEXT_BASE_PATH || "";
  return (
    <header className="site-header">
      <div className="inner">
        <a href={`${basePath}/`} className="brand">
          <span>Controls</span>
        </a>
        <nav>
          <a href={`${basePath}/checklists`}>Library</a>
          <a href={`${basePath}/submissions`}>Answered checklists</a>
        </nav>
      </div>
    </header>
  );
}
