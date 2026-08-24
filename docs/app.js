/* Pyodide wiring for the URL Genie demo.
 * Loads Pyodide from the jsdelivr CDN, installs the real "urlgenie" wheel from
 * PyPI via micropip, then defines small Python bridge functions that return
 * JSON strings -- the simplest reliable way to move dataclasses/sets across
 * the JS <-> Python boundary without fighting PyProxy conversion rules.
 */

const PYODIDE_VERSION = "0.26.4";

/* Python helpers, executed once Pyodide + urlgenie are ready. Each wraps one
 * urlgenie call and returns a JSON string so the JS side never has to deal
 * with PyProxy objects (sets, dataclasses) directly. */
const BRIDGE_SOURCE = `
import json
import urlgenie

def _bridge_generalize(url, **flags):
    result = urlgenie.generalize(url, **flags)
    social = None
    if result is not None:
        handle = urlgenie.extract_social_handle(url)
        if handle is not None:
            social = {
                "platform": handle.platform,
                "handle": handle.handle,
                "original_handle": handle.original_handle,
                "rule": handle.rule,
            }
    return json.dumps({"result": result, "social": social})

def _bridge_generalize_many(urls_text, separator, drop_invalid, **flags):
    pairs = urlgenie.generalize_many(
        urls_text, separator=separator, drop_invalid=drop_invalid, **flags
    )
    return json.dumps([{"input": original, "result": result} for original, result in pairs])

def _bridge_extract(text, include, url_filter):
    include_list = list(include) if include else None
    result = urlgenie.extract_contacts(text, include=include_list)
    if url_filter:
        result = urlgenie.validate_contacts(result, url=url_filter)
    return json.dumps({field: sorted(values) for field, values in result.as_dict().items()})

def _bridge_validate_url(url, require_suffix):
    return json.dumps({"valid": urlgenie.validate_url(url, require_suffix=require_suffix)})

def _bridge_validate_email(email, url_filter):
    return json.dumps({"valid": urlgenie.validate_email(email, url=url_filter or None)})

def _bridge_validate_phone(phone):
    normalized = urlgenie.normalize_phone(phone)
    return json.dumps({"valid": normalized is not None, "normalized": normalized})

def _bridge_validate_social(url):
    return json.dumps({"valid": urlgenie.validate_social(url)})

def _bridge_validate_social_platform(url, platform):
    return json.dumps({"valid": urlgenie.validate_social_platform(url, platform)})

def _bridge_validate_social_profile(url, platform):
    return json.dumps({"valid": urlgenie.validate_social_profile(url, platform)})
`;

let bridge = {};

function setStatus(state, text) {
  const el = document.getElementById("runtime-status");
  el.classList.remove("booting", "ready", "failed");
  el.classList.add(state);
  el.querySelector(".status-text").textContent = text;
}

function setButtonsEnabled(enabled) {
  document.querySelectorAll("button.run").forEach((btn) => (btn.disabled = !enabled));
}

async function initPyodide() {
  setStatus("booting", "Booting Python runtime…");
  try {
    const pyodide = await loadPyodide({
      indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`,
    });

    setStatus("booting", "Installing urlgenie from PyPI…");
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install("urlgenie");

    pyodide.runPython(BRIDGE_SOURCE);
    bridge = {
      generalize: pyodide.globals.get("_bridge_generalize"),
      generalizeMany: pyodide.globals.get("_bridge_generalize_many"),
      extract: pyodide.globals.get("_bridge_extract"),
      validateUrl: pyodide.globals.get("_bridge_validate_url"),
      validateEmail: pyodide.globals.get("_bridge_validate_email"),
      validatePhone: pyodide.globals.get("_bridge_validate_phone"),
      validateSocial: pyodide.globals.get("_bridge_validate_social"),
      validateSocialPlatform: pyodide.globals.get("_bridge_validate_social_platform"),
      validateSocialProfile: pyodide.globals.get("_bridge_validate_social_profile"),
    };

    const version = pyodide.runPython("import urlgenie; urlgenie.__version__");
    setStatus("ready", `Ready — running urlgenie v${version} live via Pyodide`);
    setButtonsEnabled(true);
  } catch (err) {
    console.error(err);
    setStatus("failed", "Failed to load the Python runtime — see console for details");
  }
}

/* ---------------- Tabs ---------------- */

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById("panel-" + tab.dataset.tab).classList.add("active");
    });
  });
}

/* Real single-URL rows pulled from sample.csv (52 total rows, minus section
 * headers, the one combined multi-URL row, and one row containing a literal
 * "<numbers>" template placeholder that isn't a runnable example). */
const EXAMPLE_URLS = [
  "fb.com/@ahmedkhatib",
  "facebook.com/ahmedkhatib..90/about?idk=idk#some_fragment",
  "facebook.com/@ahmedkhatib",
  "facebook.com/pg/123123123",
  "facebook.com/pg/ahmedkhatib",
  "facebook.com/watch/ahmedkhatib",
  "facebook.com/events/12312312",
  "facebook.com/#!/ahmedkhatib",
  "facebook.com/home.php#/ahmedkhatib",
  "facebook.com/home.php?#!/ahmedkhatib",
  "facebook.com/?ref=home#!/ahmedkhatib",
  "facebook.com/?ref=tn_tnmn#!/ahmedkhatib",
  "facebook.com/?sk=lf#!/ahmedkhatib",
  "facebook.com/?ref=logo#!/ahmedkhatib",
  "facebook.com/?_rdr#!/ahmedkhatib",
  "facebook.com/pages/category/Journalist/ahmedkhatib",
  "facebook.com/pages/category/photographer/ahmedkhatib-123123123",
  "facebook.com/Ahmed-Khatib-123123123",
  "facebook.com/group.php?gid=123123123",
  "facebook.com/profile.php?ref=name&id=123123123",
  "facebook.com/pages/Ahmed-Khatib/123123123",
  "facebook.com/groups/groupid/user/123123123",
  "facebook.com/pages/edit/?id=123123123",
  "facebook.com.br/ahmedkhatib",
  "facebook.com.au/ahmedkhatib",
  "www.secure.latest.facebook.com.au/#!/pages/Ahmed-Khatib/123123123?some=query#some_fragment",
  "facebook.com/media/set/?set=a.1386330472434.107549.123123123",
  "linkedin.com/in/ahmedkhatib-99/about/anythinggoeshere?keyvalue&something#somefragments",
  "https://www.linkedin.com/in/marie-zaarour-hanna-%D9%85%D8%A7%D8%B1%D9%8A-%D8%B2%D8%B9%D8%B1%D9%88%D8%B1-%D8%AD%D9%86%D8%A7-85600546/",
  "https://www.linkedin.com/pub/mark-adams/28/1b8/a?_l=en_US",
  "https://www.linkedin.com/groups/Wholesaler-magazine-4806067/",
  "https://www.linkedin.com/company-beta/1961897/",
  "https://www.linkedin.com/organization-guest/company/australasian-convenience-and-petroleum-marketers-association-acapma-?challengeId=AQG1JHkLLbFJGwAAAXE3xGRkpBzAAQGtv84mB_SGzYhWjQvvjRCJI6CRD90q_eLgpl6MzRpOYpwReAp7i1AyDk_5RLN4Q683xQ&submissionId=fd14346a-30d1-0116-c503-266d810a021e",
  "http://www.linkedin.com/groupInvitation?gID=3927197",
  "http://www.linkedin.com/companies/bdc?trk=fc_badge",
  "https://www.linkedin.com/edu/school?id=19647&trk=tyah&trkInfo=tas%3APacific%20Lutheran%20%2Cidx%3A3-1-4",
  "https://ie.linkedin.com/edu/trinity-college-dublin-13378",
  "https://www.linkedin.com/organization/13355989/",
  "https://www.LinkedIn.com/in/ACwAAAxF1hwBy6_9YpmhkW1pUuOxHiYnko3qYjg/",
  "https://linkedin.com/showcase/tacomarine/",
  "http://www.linkedin.com/showcase/18007651/",
  "https://www.linkedin.com/grps/LBM-Journal-Group-2308936/",
  "https://www.linkedin.com.au/edu/school?id=18761&trk=edu-cp-title",
  "https://www.linkedin.com.br/in/inahul-jOsHi-915b9a12a/",
  "x.com/elonmusk",
  "twitter.com/ahmedkhatib/about/anythinggoeshere?keyvalue&something#somefragments",
  "twitter.com/@ahmedkhatib",
  "twitter.com/intent/follow?original_referer=&screen_name=ahmedkhatib",
  "instagram.com/ahmedkhatib/about/anythinggoeshere?keyvalue&something#somefragments",
  "instagram.com/accounts/login/?next=/ahmedkhatib/",
  "cnn.com/sports/about/anythinggoeshere?keyvalue&something#somefragments",
];

let exampleBag = [];

function nextExampleUrl() {
  if (exampleBag.length === 0) {
    exampleBag = [...EXAMPLE_URLS];
    // Fisher-Yates shuffle -- every URL appears exactly once per pass through the bag.
    for (let i = exampleBag.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [exampleBag[i], exampleBag[j]] = [exampleBag[j], exampleBag[i]];
    }
  }
  return exampleBag.pop();
}

function fillExample(inputId) {
  document.getElementById(inputId).value = nextExampleUrl();
}

/* ---------------- Validate tab ---------------- */

function showValidateResult(resultId, valid, extraText, label) {
  const el = document.getElementById(resultId);
  el.innerHTML = "";
  const badge = document.createElement("span");
  badge.className = valid ? "badge-valid" : "badge-invalid";
  badge.textContent = (label ? `${label}: ` : "") + (valid ? "✓ Valid" : "✗ Invalid");
  el.appendChild(badge);
  if (extraText) {
    const note = document.createElement("span");
    note.className = "chip";
    note.style.marginLeft = "8px";
    note.textContent = extraText;
    el.appendChild(note);
  }
}

function showValidateError(resultId, err) {
  console.error(err);
  const el = document.getElementById(resultId);
  el.innerHTML = "";
  const badge = document.createElement("span");
  badge.className = "badge-invalid";
  badge.textContent = "⚠ Error — see console";
  el.appendChild(badge);
}

function initValidateTab() {
  document.getElementById("val-url-btn").addEventListener("click", () => {
    try {
      const url = document.getElementById("val-url-input").value.trim();
      const requireSuffix = document.getElementById("val-url-require-suffix").checked;
      const raw = bridge.validateUrl.callKwargs(url, { require_suffix: requireSuffix });
      const data = JSON.parse(raw);
      showValidateResult("val-url-result", data.valid);
    } catch (err) {
      showValidateError("val-url-result", err);
    }
  });

  document.getElementById("val-email-btn").addEventListener("click", () => {
    try {
      const email = document.getElementById("val-email-input").value.trim();
      const useDomain = document.getElementById("val-email-domain-check").checked;
      const domainUrl = useDomain ? document.getElementById("val-email-domain-input").value.trim() : "";
      const raw = bridge.validateEmail.callKwargs(email, { url_filter: domainUrl });
      const data = JSON.parse(raw);
      showValidateResult("val-email-result", data.valid);
    } catch (err) {
      showValidateError("val-email-result", err);
    }
  });

  document.getElementById("val-phone-btn").addEventListener("click", () => {
    try {
      const phone = document.getElementById("val-phone-input").value.trim();
      const raw = bridge.validatePhone.callKwargs(phone, {});
      const data = JSON.parse(raw);
      showValidateResult("val-phone-result", data.valid);
      document.getElementById("val-phone-normalized").value = data.valid ? data.normalized : "";
    } catch (err) {
      showValidateError("val-phone-result", err);
      document.getElementById("val-phone-normalized").value = "";
    }
  });

  document.getElementById("val-social-btn").addEventListener("click", () => {
    try {
      const url = document.getElementById("val-social-input").value.trim();
      const raw = bridge.validateSocial.callKwargs(url, {});
      const data = JSON.parse(raw);
      showValidateResult("val-social-result", data.valid);
    } catch (err) {
      showValidateError("val-social-result", err);
    }
  });

  document.getElementById("val-platform-btn").addEventListener("click", () => {
    try {
      const url = document.getElementById("val-platform-input").value.trim();
      const platform = document.getElementById("val-platform-select").value;
      const raw = bridge.validateSocialPlatform.callKwargs(url, { platform });
      showValidateResult("val-platform-result", JSON.parse(raw).valid);
    } catch (err) {
      showValidateError("val-platform-result", err);
    }
  });

  document.getElementById("val-profile-btn").addEventListener("click", () => {
    try {
      const url = document.getElementById("val-profile-input").value.trim();
      const platform = document.getElementById("val-profile-select").value;
      const raw = bridge.validateSocialProfile.callKwargs(url, { platform });
      showValidateResult("val-profile-result", JSON.parse(raw).valid);
    } catch (err) {
      showValidateError("val-profile-result", err);
    }
  });
}

/* ---------------- Generalize tab ---------------- */

function readGeneralizeFlags(prefix) {
  return {
    social: document.getElementById(`${prefix}-social`).checked,
    keep_query: document.getElementById(`${prefix}-keep-query`).checked,
    keep_fragment: document.getElementById(`${prefix}-keep-fragment`).checked,
    lower: document.getElementById(`${prefix}-lower`).checked,
    keep_path: document.getElementById(`${prefix}-keep-path`).checked,
    keep_userinfo: document.getElementById(`${prefix}-keep-userinfo`).checked,
    force_https: document.getElementById(`${prefix}-force-https`).checked,
  };
}

function initGeneralizeTab() {
  document.getElementById("gen-btn").addEventListener("click", () => {
    const url = document.getElementById("gen-input").value.trim();
    const flags = readGeneralizeFlags("gen");
    const card = document.getElementById("gen-result");
    card.classList.remove("hidden");

    try {
      const raw = bridge.generalize.callKwargs(url, flags);
      const data = JSON.parse(raw);

      const main = document.getElementById("gen-result-main");
      main.innerHTML = "";
      main.append(url, " ");
      const arrow = document.createElement("span");
      arrow.className = "arrow";
      arrow.textContent = "→";
      main.appendChild(arrow);
      const outSpan = document.createElement("span");
      outSpan.className = data.result === null ? "bad" : "ok";
      outSpan.textContent = data.result === null ? "Invalid / not recognized" : data.result;
      main.appendChild(outSpan);

      const chips = document.getElementById("gen-result-chips");
      const note = document.getElementById("gen-result-note");
      chips.innerHTML = "";
      note.textContent = "";

      if (data.social) {
        const s = data.social;
        chips.innerHTML = `
          <div class="chip">platform: <b>${s.platform}</b></div>
          <div class="chip">handle: <b>${s.handle}</b></div>
          <div class="chip">original handle: <b>${s.original_handle}</b></div>
          <div class="chip">rule matched: <b>${s.rule}</b></div>`;
        note.textContent = "Recognized as a social profile — the flags above were ignored for this result.";
      }
    } catch (err) {
      console.error(err);
      document.getElementById("gen-result-main").textContent = "Something went wrong — see console.";
    }
  });
}

/* ---------------- Generalize Many tab ---------------- */

/* Groups rows by their result. Every valid result gets an entry; results that
 * occur more than once additionally get a stable "A", "B", "C", ... label, so
 * on-screen badges, the export, and any other consumer of this data always
 * agree on which rows belong to the same group -- one source of truth instead
 * of three separate implementations that could drift. */
const DUP_COLORS = ["#6cb2ff", "#f7b955", "#c792ea", "#4fc766", "#ff8fa3", "#5fd4d0"];

function computeDuplicateGroups(rows) {
  const counts = new Map();
  rows.forEach((row) => {
    if (row.result !== null) counts.set(row.result, (counts.get(row.result) || 0) + 1);
  });

  const labels = new Map();
  const colors = new Map();
  let next = 0;
  counts.forEach((count, result) => {
    if (count > 1) {
      let label = "";
      let n = next;
      do {
        label = String.fromCharCode(65 + (n % 26)) + label;
        n = Math.floor(n / 26) - 1;
      } while (n >= 0);
      labels.set(result, label);
      colors.set(result, DUP_COLORS[next % DUP_COLORS.length]);
      next++;
    }
  });

  return { counts, labels, colors };
}

function initGeneralizeManyTab() {
  document.getElementById("many-btn").addEventListener("click", () => {
    const rawText = document.getElementById("many-input").value;
    const separator = document.getElementById("many-separator").value || ",";
    const dropInvalid = document.getElementById("many-drop-invalid").checked;
    const flags = readGeneralizeFlags("many");
    const card = document.getElementById("many-result");
    card.classList.remove("hidden");

    // Accept one-per-line AND separator-delimited input regardless of which
    // the separator field is set to, by folding newlines into the separator
    // before generalize_many() only ever has to split on one character.
    const text = rawText.replace(/\r?\n/g, separator);

    const groupDuplicates = document.getElementById("many-group-duplicates").checked;
    const errorEl = document.getElementById("many-error");
    errorEl.style.display = "none";

    try {
      const raw = bridge.generalizeMany.callKwargs(text, separator, dropInvalid, flags);
      const rows = JSON.parse(raw);

      // A URL that looks nothing like another one can still be the same
      // profile -- this is generalize_many() doing duplicate detection, not a
      // separate feature.
      const { counts: resultCounts, labels, colors } = computeDuplicateGroups(rows);

      // Rows keep their original order and position unless "Group duplicates
      // together" is on, same guarantee as the invalid-row fix otherwise.
      // The export mirrors this exact order (see buildManyExportRows below),
      // so what you download always matches what's on screen -- uncheck the
      // grouping toggle if you want the export back in input order.
      let displayRows = rows;
      if (groupDuplicates) {
        displayRows = [...rows].sort((a, b) => {
          const keyA = a.result !== null && labels.has(a.result) ? labels.get(a.result) : "\uFFFF";
          const keyB = b.result !== null && labels.has(b.result) ? labels.get(b.result) : "\uFFFF";
          return keyA < keyB ? -1 : keyA > keyB ? 1 : 0;
        });
      }

      const tbody = document.getElementById("many-table-body");
      tbody.innerHTML = "";
      let validCount = 0;
      displayRows.forEach((row) => {
        const tr = document.createElement("tr");
        const tdIn = document.createElement("td");
        tdIn.textContent = row.input;
        const tdOut = document.createElement("td");
        if (row.result === null) {
          tdOut.innerHTML = '<span class="badge-invalid">✗ invalid</span>';
        } else {
          validCount++;
          tdOut.textContent = row.result;
          const label = labels.get(row.result);
          if (label) {
            const color = colors.get(row.result);
            const others = rows.filter((r) => r.result === row.result && r.input !== row.input).map((r) => r.input);
            const dup = document.createElement("span");
            dup.className = "dup-badge";
            dup.style.color = color;
            dup.style.borderColor = color;
            dup.style.background = color + "22";
            dup.textContent = `● ${label}`;
            dup.title = `Also seen as: ${others.join(", ")}`;
            tdOut.appendChild(document.createTextNode(" "));
            tdOut.appendChild(dup);
          }
        }
        tr.append(tdIn, tdOut);
        tbody.appendChild(tr);
      });

      const uniqueCount = resultCounts.size;
      const duplicateGroups = [...resultCounts.values()].filter((c) => c > 1).length;
      let summary = `${validCount} of ${rows.length} valid`;
      if (duplicateGroups > 0) {
        summary += ` — ${uniqueCount} unique profile${uniqueCount === 1 ? "" : "s"} (${duplicateGroups} duplicate group${duplicateGroups === 1 ? "" : "s"})`;
      }
      document.getElementById("many-summary").textContent = summary;

      const groupsEl = document.getElementById("many-dup-groups");
      if (duplicateGroups > 0) {
        const items = [...labels.entries()].sort((a, b) => (a[1] < b[1] ? -1 : 1));
        groupsEl.innerHTML =
          `<div class="dup-groups-title">Duplicate groups (${duplicateGroups})</div>` +
          items
            .map(([result, label]) => {
              const color = colors.get(result);
              const count = resultCounts.get(result);
              return `<div class="dup-group-item">
                <span class="dup-swatch" style="background:${color}"></span>
                <b>Group ${label}</b> (${count} rows) → <code>${escapeHtml(result)}</code>
              </div>`;
            })
            .join("");
      } else {
        groupsEl.innerHTML = "";
      }

      card.dataset.rows = JSON.stringify(displayRows); // exactly what's rendered, so export matches the table
    } catch (err) {
      console.error(err);
      errorEl.textContent = "Something went wrong — see the browser console for details.";
      errorEl.style.display = "block";
    }
  });

  function buildManyExportRows() {
    const raw = document.getElementById("many-result").dataset.rows;
    if (!raw) return null;
    const rows = JSON.parse(raw);
    const includeDuplicateColumns = document.getElementById("many-export-duplicates").checked;

    if (!includeDuplicateColumns) {
      return [["input", "result"], ...rows.map((r) => [r.input, r.result ?? ""])];
    }

    const { counts, labels } = computeDuplicateGroups(rows);
    const header = ["input", "result", "duplicate_group", "duplicate_count"];
    const body = rows.map((r) => [
      r.input,
      r.result ?? "",
      r.result !== null ? labels.get(r.result) || "" : "",
      r.result !== null ? counts.get(r.result) : "",
    ]);
    return [header, ...body];
  }

  document.getElementById("many-copy-btn").addEventListener("click", () => {
    const tableRows = buildManyExportRows();
    if (!tableRows) return;
    const format = document.getElementById("many-export-format").value;
    const delimited = rowsToDelimited(tableRows, format === "tsv" ? "\t" : ",");
    copyText(delimited, document.getElementById("many-copy-feedback"));
  });

  document.getElementById("many-download-btn").addEventListener("click", () => {
    const tableRows = buildManyExportRows();
    if (!tableRows) return;
    const format = document.getElementById("many-export-format").value;
    const delimited = rowsToDelimited(tableRows, format === "tsv" ? "\t" : ",");
    downloadText(`urlgenie-generalized.${format}`, delimited, format === "tsv" ? "text/tab-separated-values" : "text/csv");
  });
}

/* ---------------- Extract Data tab ---------------- */

const EXTRACT_CATEGORIES = ["emails", "phones", "facebook", "twitter", "instagram", "linkedin", "youtube"];

function initExtractTab() {
  document.getElementById("extract-btn").addEventListener("click", () => {
    const text = document.getElementById("extract-input").value;
    const include = EXTRACT_CATEGORIES.filter(
      (cat) => document.getElementById(`extract-cat-${cat}`).checked
    );
    const useDomain = document.getElementById("extract-domain-check").checked;
    const domainUrl = useDomain ? document.getElementById("extract-domain-input").value.trim() : "";
    const card = document.getElementById("extract-result");
    card.classList.remove("hidden");
    const errorEl = document.getElementById("extract-error");
    errorEl.style.display = "none";

    try {
      const raw = bridge.extract(text, include, domainUrl);
      const data = JSON.parse(raw);

      EXTRACT_CATEGORIES.forEach((cat) => {
        const container = document.getElementById(`extract-chips-${cat}`);
        const values = data[cat] || [];
        container.innerHTML = values.length
          ? values.map((v) => `<div class="chip">${escapeHtml(v)}</div>`).join("")
          : '<div class="empty">None found</div>';
      });
      card.dataset.result = raw;
    } catch (err) {
      console.error(err);
      errorEl.textContent = "Something went wrong — see the browser console for details.";
      errorEl.style.display = "block";
    }
  });

  document.getElementById("extract-copy-btn").addEventListener("click", () => {
    const raw = document.getElementById("extract-result").dataset.result;
    if (!raw) return;
    const format = document.getElementById("extract-export-format").value;
    const keepEmpty = document.getElementById("extract-keep-empty").checked;
    const delimited = rowsToDelimited(buildExtractExportRows(JSON.parse(raw), keepEmpty), format === "tsv" ? "\t" : ",");
    copyText(delimited, document.getElementById("extract-copy-feedback"));
  });

  document.getElementById("extract-download-btn").addEventListener("click", () => {
    const raw = document.getElementById("extract-result").dataset.result;
    if (!raw) return;
    const format = document.getElementById("extract-export-format").value;
    const keepEmpty = document.getElementById("extract-keep-empty").checked;
    const delimited = rowsToDelimited(buildExtractExportRows(JSON.parse(raw), keepEmpty), format === "tsv" ? "\t" : ",");
    downloadText(`urlgenie-contacts.${format}`, delimited, format === "tsv" ? "text/tab-separated-values" : "text/csv");
  });
}

/* One column per category (emails, phones, facebook, ...) instead of a
 * type/value pair per row. Categories don't have the same number of results,
 * so short columns are padded with blank cells rather than forcing every
 * column to the same length by truncating or repeating values.
 *
 * keepEmpty=false (default): categories with zero results are omitted from
 * the header entirely, so the export only has columns that actually found
 * something. keepEmpty=true: every category gets a column, in a fixed order,
 * even if it's entirely blank -- useful when exporting more than once and
 * wanting the same column layout every time. */
function buildExtractExportRows(data, keepEmpty) {
  const categories = keepEmpty
    ? EXTRACT_CATEGORIES
    : EXTRACT_CATEGORIES.filter((cat) => (data[cat] || []).length > 0);

  const maxRows = categories.reduce((max, cat) => Math.max(max, (data[cat] || []).length), 0);
  const body = [];
  for (let i = 0; i < maxRows; i++) {
    body.push(categories.map((cat) => (data[cat] || [])[i] ?? ""));
  }
  return [categories, ...body];
}

/* ---------------- CSV/TSV + clipboard/download helpers ---------------- */

function escapeField(value, delimiter) {
  const str = String(value ?? "");
  if (str.includes(delimiter) || str.includes('"') || str.includes("\n") || str.includes("\r")) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function rowsToDelimited(rows, delimiter) {
  return rows.map((row) => row.map((field) => escapeField(field, delimiter)).join(delimiter)).join("\r\n");
}

function downloadText(filename, text, mime) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function copyText(text, feedbackEl) {
  try {
    await navigator.clipboard.writeText(text);
    feedbackEl.textContent = "Copied!";
  } catch (err) {
    feedbackEl.textContent = "Copy failed";
  }
  feedbackEl.classList.add("show");
  setTimeout(() => feedbackEl.classList.remove("show"), 1500);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ---------------- Boot ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initValidateTab();
  initGeneralizeTab();
  initGeneralizeManyTab();
  initExtractTab();
  setButtonsEnabled(false);
  initPyodide();
});
