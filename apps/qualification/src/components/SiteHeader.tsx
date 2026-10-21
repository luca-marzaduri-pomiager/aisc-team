import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="site-header">
      <div className="inner">
        <Link href="/" className="brand">
          <span>Qualification</span>
        </Link>
      </div>
    </header>
  );
}
