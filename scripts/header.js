function loadHeader() {

  var header_names = ['about', 'goals', 'news', 'publications']; // vision blog

  // Detect current page
  var path = window.location.pathname;
  var current = ''; // default

  for (var i = 0; i < header_names.length; i++) {
    if (path.indexOf(header_names[i]) !== -1) {
      current = header_names[i];
    }
  }

  // Build the menu items
  var parts = [];
  for (var i = 0; i < header_names.length; i++) {
    var name = header_names[i];

    if (name === current) {
      // Active page → not a link
      parts.push('<span class="active-page">' + name + '</span>');
    } else {
      // Other pages → normal links
      parts.push('<a href="./' + name + '.html" class="inactive-page">' + name + '</a>');
    }
  }

  var headerLinks = parts.join(' · ');

  var headerHTML = ''
    + '<header>'
    +   '<div class="title">'
    +     '<img src="assets/logo.png" alt="logo">'
    +     '<div>'
    +       '<main>dreamstimlab</main>'
    +       '<sub>non-invasive neural interfacing for dream I/O</sub>'
    +     '</div>'
    +   '</div>'
    +   '<div class="center">'
    +     headerLinks
    +   '</div>'
    + '</header>';

  document.body.insertAdjacentHTML('afterbegin', headerHTML);
}

// window.onload = loadHeader;
loadHeader();