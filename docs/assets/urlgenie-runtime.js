// Loads Pyodide and installs the real urlgenie wheel — explanations come from urlgenie.explain.
// Every answer the pages show comes back from this file — there is no JS fallback.

const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';

const BRIDGE = `
import json, urlgenie as ug
from urlgenie import explain
from urlgenie.social import extract_social_handle

def __api(name, payload):
    a = json.loads(payload)
    if name == "url":       out = explain.explain_url(a["v"]).as_dict()
    elif name == "email":   out = explain.explain_email(a["v"], url=a.get("site") or None).as_dict()
    elif name == "phone":   out = explain.explain_phone(a["v"]).as_dict()
    elif name == "social":  out = explain.explain_social(a["v"]).as_dict()
    elif name == "platform":out = explain.explain_social_platform(a["v"], a["p"]).as_dict()
    elif name == "profile": out = explain.explain_social_profile(a["v"], a["p"]).as_dict()
    elif name == "generalize":
        flags = a.get("flags") or {}
        result = ug.generalize(a["v"], **flags)
        if result is None:
            out = {"ok": False, "message": explain.MESSAGES["generalize.invalid"], "detail": ""}
        else:
            handle = extract_social_handle(a["v"]) if flags.get("social", True) else None
            if handle is not None:
                out = {"ok": True, "message": explain.MESSAGES["generalize.social"].format(platform=handle.platform), "detail": result}
            else:
                out = {"ok": True, "message": explain.MESSAGES["generalize.ok"], "detail": result}
    elif name == "many":
        pairs = ug.generalize_many([l for l in a["v"].replace(",", "\\n").split("\\n") if l.strip()])
        groups = {}
        invalid = []
        for original, generalized in pairs:
            # None keys would otherwise all collapse into one dict bucket,
            # showing unrelated invalid rows as if they were duplicates of
            # each other. Each invalid input gets its own group of one.
            if generalized is None:
                invalid.append(original)
            else:
                groups.setdefault(generalized, []).append(original)
        out_groups = [{"canon": k, "inputs": v, "count": len(v), "ok": True} for k, v in groups.items()]
        out_groups += [{"canon": None, "inputs": [o], "count": 1, "ok": False} for o in invalid]
        out = {"total": len(pairs), "groups": out_groups}
    elif name == "extract":
        r = ug.extract_contacts(a["v"])
        out = {"emails": sorted(r.emails), "phones": sorted(r.phones), "facebook": sorted(r.facebook),
               "twitter": sorted(r.twitter), "instagram": sorted(r.instagram),
               "linkedin": sorted(r.linkedin), "youtube": sorted(r.youtube)}
    elif name == "platforms":
        from urlgenie.config import PLATFORMS
        out = sorted({p.name for p in PLATFORMS})
    else:
        raise ValueError(name)
    return json.dumps(out)

__version = ug.__version__
`;

let booting = null;

function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = src; s.onload = res; s.onerror = () => rej(new Error('could not load ' + src));
    document.head.appendChild(s);
  });
}

export function boot(onStatus) {
  if (booting) return booting;
  const say = onStatus || (() => {});
  booting = (async () => {
    say('loading Python runtime');
    if (!window.loadPyodide) await loadScript(PYODIDE + 'pyodide.js');
    const py = await window.loadPyodide({ indexURL: PYODIDE });
    say('installing urlgenie');
    await py.loadPackage('micropip');
    await py.pyimport('micropip').install('urlgenie');
    say('loading explanations');
    py.runPython(BRIDGE);
    const version = py.globals.get('__version');
    const api = py.globals.get('__api');
    say('ready');
    return {
      version,
      call: (name, args) => JSON.parse(api(name, JSON.stringify(args)))
    };
  })();
  return booting;
}
