/*
 * Ponte tra la pagina e l'app Android.
 *
 * Streamlit scarica i file (Excel, backup, PNG dei grafici) creando un link
 * <a download> verso un blob: o data: URL. La WebView di Android non sa
 * salvarli da sola: qui intercettiamo quei clic e passiamo il contenuto
 * all'app nativa (window.FTAndroid.saveFile), che lo salva in Download.
 *
 * Fuori dall'app (es. test nel browser) window.FTAndroid non esiste
 * e questo script non fa nulla.
 */
(function () {
  "use strict";

  var bridge = window.FTAndroid;
  if (!bridge || typeof bridge.saveFile !== "function") return;

  // Streamlit revoca il blob: URL subito dopo il clic, quindi teniamo
  // un riferimento al Blob per poterlo leggere anche dopo.
  var blobs = new Map();
  var originalCreate = URL.createObjectURL.bind(URL);
  var originalRevoke = URL.revokeObjectURL.bind(URL);

  URL.createObjectURL = function (obj) {
    var url = originalCreate(obj);
    if (obj instanceof Blob) blobs.set(url, obj);
    return url;
  };

  URL.revokeObjectURL = function (url) {
    // Il Blob resta in memoria ancora un minuto, il tempo di salvarlo.
    setTimeout(function () {
      blobs.delete(url);
      originalRevoke(url);
    }, 60000);
  };

  function isDownloadable(href) {
    if (typeof href !== "string" || href === "") return false;
    if (href.indexOf("blob:") === 0 || href.indexOf("data:") === 0) return true;
    try {
      // Link della stessa app (es. /media/... di Streamlit).
      return new URL(href, location.href).origin === location.origin;
    } catch (error) {
      return false;
    }
  }

  function readAsBase64(blob) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var result = String(reader.result || "");
        resolve(result.slice(result.indexOf(",") + 1));
      };
      reader.onerror = function () { reject(reader.error); };
      reader.readAsDataURL(blob);
    });
  }

  function fileNameFromDisposition(header) {
    if (!header) return "";
    var star = /filename\*\s*=\s*(?:UTF-8'')?([^;]+)/i.exec(header);
    if (star) {
      try { return decodeURIComponent(star[1].trim().replace(/^"|"$/g, "")); } catch (e) { /* ignora */ }
    }
    var plain = /filename\s*=\s*"?([^";]+)"?/i.exec(header);
    return plain ? plain[1].trim() : "";
  }

  // Restituisce { blob, name }: il nome arriva dal link o, se manca,
  // dall'intestazione Content-Disposition della risposta.
  function resolveDownload(href, fileName) {
    if (blobs.has(href)) {
      return Promise.resolve({ blob: blobs.get(href), name: fileName });
    }
    return fetch(href).then(function (response) {
      var name = fileName || fileNameFromDisposition(response.headers.get("Content-Disposition"));
      return response.blob().then(function (blob) {
        return { blob: blob, name: name };
      });
    });
  }

  function save(href, fileName) {
    resolveDownload(href, fileName)
      .then(function (result) {
        return readAsBase64(result.blob).then(function (base64) {
          bridge.saveFile(
            result.name || "FinanceTracker_download",
            result.blob.type || "application/octet-stream",
            base64
          );
        });
      })
      .catch(function (error) {
        if (typeof bridge.toast === "function") {
          bridge.toast("Download non riuscito: " + error);
        }
      });
  }

  // Link creati e cliccati via codice (anche fuori dal DOM).
  var originalClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    if (this.hasAttribute("download") && isDownloadable(this.href)) {
      save(this.href, this.getAttribute("download"));
      return;
    }
    return originalClick.call(this);
  };

  // Link <a download> toccati dall'utente.
  document.addEventListener(
    "click",
    function (event) {
      var target = event.target;
      var anchor = target && target.closest ? target.closest("a[download]") : null;
      if (anchor && isDownloadable(anchor.href)) {
        event.preventDefault();
        save(anchor.href, anchor.getAttribute("download"));
      }
    },
    true
  );
})();
