import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.left}>
          <div className={styles.logo}>
            <span className={styles.icon}>⚔️</span>
            <span className={styles.name}>QuoteShield</span>
          </div>
          <span className={styles.badge}>Open-source AI · Groq</span>
        </div>
        <p className={styles.tagline}>Paste the chaos. Get a watertight scope.</p>
      </div>
    </header>
  )
}
