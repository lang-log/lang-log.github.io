'use strict';
// Used by the pages left at the old t/... URLs (written by build_paths.py).
// Sends the visitor to the new URL at once and keeps the #anchor, which the
// meta refresh fallback would drop (for example t/.../english/#old).
(()=>{const c=document.querySelector('link[rel="canonical"]');if(c)location.replace(c.href+location.hash)})();
