const headerHTML = `
<header class="site-header">
  <div class="header-container">
    <a href="music-ide.html" class="logo">Music DSL</a>
    <nav>
      <ul class="nav-menu" id="navMenu">
        <li><a href="music-ide.html">Home</a></li>
        <li><a href="music-library.html">Library</a></li>
        <li><a href="mysong_sheet.html">Music Sheets</a></li>
        <li><a href="music-instructions.html">Instructions</a></li>
      </ul>
      <button class="mobile-menu-toggle" id="mobileToggle">☰</button>
    </nav>
  </div>
</header>

<style>
.site-header {
  background: linear-gradient(to right, #4e54c8, #8f94fb);
  padding: 1rem 2rem;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-menu {
  list-style: none;
  display: flex;
  gap: 1.5rem;
  margin: 0;
  padding: 0;
}

.nav-menu li a {
  text-decoration: none;
  color: white;
  font-weight: 500;
  transition: color 0.3s;
}

.nav-menu li a:hover,
.nav-menu li a.active {
  color: #dcdcff;
}

.mobile-menu-toggle {
  display: none;
  background: none;
  font-size: 1.5rem;
  border: none;
  color: white;
  cursor: pointer;
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
    flex-direction: column;
    background-color: #4e54c8;
    padding: 1rem;
    position: absolute;
    top: 60px;
    right: 20px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  }

  .nav-menu.active {
    display: flex;
  }

  .mobile-menu-toggle {
    display: block;
  }
}
</style>
`;

const footerHTML = `
<footer class="site-footer">
  <div class="footer-container">
    <div class="footer-content">
      <div class="footer-section">
        <h3>Quick Links</h3>
        <ul>
          <li><a href="music-ide.html">Music DSL Web IDE</a></li>
          <li><a href="music-ide.html">Home</a></li>
          <li><a href="music-library.html">Library</a></li>
          <li><a href="mysong_sheet.html">Music Sheets</a></li>
          <li><a href="music-instructions.html">Instructions</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Contact Info</h3>
        <ul>
          <li>Amza Vladislav, <a href="mailto:vladislav.amza@isa.utm.md">vladislav.amza@isa.utm.md</a></li>
          <li>Chirpicinic Madalina, <a href="mailto:madalina.chirpicinic@isa.utm.md">madalina.chirpicinic@isa.utm.md</a></li>
          <li>Popescu Sabina, <a href="mailto:sabina.popescu@isa.utm.md">sabina.popescu@isa.utm.md</a></li>
          <li>Postoronca Dumitru, <a href="mailto:dumitru.postoronca@isa.utm.md">dumitru.postoronca@isa.utm.md</a></li>
          <li>Racovita Dumitru, <a href="mailto:dumitru.racovita@isa.utm.md">dumitru.racovita@isa.utm.md</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2025 MusicDSL. All rights reserved.</p>
    </div>
  </div>
</footer>

<style>
.site-footer {
  background-color: #2c2f4a;
  color: #ccc;
  padding: 2rem;
  text-align: center;
}

.footer-container {
  max-width: 1200px;
  margin: auto;
}

.footer-content {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-around;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.footer-section h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.footer-section ul {
  list-style: none;
  padding: 0;
}

.footer-section li {
  margin-bottom: 0.5rem;
}

.footer-section a {
  text-decoration: none;
  color: #ccc;
  transition: color 0.3s;
}

.footer-section a:hover {
  color: white;
}

.footer-bottom {
  border-top: 1px solid #444;
  padding-top: 1rem;
  font-size: 0.9rem;
}
</style>
`;

document.addEventListener("DOMContentLoaded", () => {
  const headerPlaceholder = document.getElementById("header-placeholder");
  if (headerPlaceholder) {
    headerPlaceholder.innerHTML = headerHTML;
  }

  const footerPlaceholder = document.getElementById("footer-placeholder");
  if (footerPlaceholder) {
    footerPlaceholder.innerHTML = footerHTML;
  }

  initializeMobileMenu();
  setActiveNavItem();
});

function initializeMobileMenu() {
  const mobileToggle = document.getElementById("mobileToggle");
  const navMenu = document.getElementById("navMenu");

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener("click", () => {
      navMenu.classList.toggle("active");
    });

    navMenu.addEventListener("click", (e) => {
      if (e.target.tagName === "A") {
        navMenu.classList.remove("active");
      }
    });
  }
}

function setActiveNavItem() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll(".nav-menu a");

  navLinks.forEach((link) => {
    link.classList.remove("active");
    const linkPath = new URL(link.href).pathname;
    if (currentPath === linkPath) {
      link.classList.add("active");
    }
  });
}
