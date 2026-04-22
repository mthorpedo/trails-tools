(function () {
  "use strict";

  // Game ids from <select id="game">: sky-fc, sky-sc, sky-tc are the Sky trilogy; zero is Crossbell (Trails from Zero).

  const ELEMENTS = ["earth", "water", "fire", "wind", "time", "space", "mirage"];

  /** Quartz names that may appear in more than one slot at once (bypass type exclusivity). */
  const QUARTZ_ALLOW_DUPLICATE_ACROSS_SLOTS = new Set(["Heal", "Yin-Yang"]);

  function quartzAllowsDuplicateAcrossSlots(q) {
    return q && QUARTZ_ALLOW_DUPLICATE_ACROSS_SLOTS.has(q.name);
  }

  const gameSelect = document.getElementById("game");
  const characterSelect = document.getElementById("character");
  const panel = document.getElementById("character-panel");
  const slotsBody = document.querySelector("#orbment-slots tbody");
  const lineBody = document.querySelector("#line-totals tbody");
  const lineEmptyMsg = document.getElementById("line-totals-empty");
  const artsBody = document.querySelector("#arts-enabled tbody");
  const artsEmptyMsg = document.getElementById("arts-enabled-empty");
  const loadError = document.getElementById("load-error");

  let characters = [];
  let quartzList = [];
  let artsList = [];

  function showError(msg) {
    loadError.textContent = msg;
    loadError.classList.remove("hidden");
  }

  function clearError() {
    loadError.textContent = "";
    loadError.classList.add("hidden");
  }

  function elementalClass(el) {
    if (!el) return "neutral";
    const k = String(el).toLowerCase();
    if (ELEMENTS.indexOf(k) >= 0) return "elemental-" + k;
    return "neutral";
  }

  /** Background for orbment table column 2 (quartz) by slot line number. */
  function quartzLineClass(line) {
    if (line === 1) return "quartz-slot-line-1";
    if (line === 2) return "quartz-slot-line-2";
    if (line === 3) return "quartz-slot-line-3";
    if (line === 4) return "quartz-slot-line-4";
    return "";
  }

  function zeroRow() {
    const o = {};
    ELEMENTS.forEach(function (e) {
      o[e] = 0;
    });
    return o;
  }

  function distinctPositiveLines(orbment) {
    const s = new Set();
    orbment.forEach(function (slot) {
      if (slot.line > 0) s.add(slot.line);
    });
    return Array.from(s).sort(function (a, b) {
      return a - b;
    });
  }

  /** Types taken by quartz selected on other slots (not `excludeSlotIndex`). */
  function usedTypesExceptSlot(excludeSlotIndex, slotValues) {
    const used = new Set();
    slotValues.forEach(function (v, j) {
      if (j === excludeSlotIndex || v === "") return;
      const q = quartzList[parseInt(v, 10)];
      if (q && !quartzAllowsDuplicateAcrossSlots(q)) used.add(Number(q.type));
    });
    return used;
  }

  /** If multiple slots selected quartz of the same type, keep first slot, clear later ones. */
  function resolveConflictingSelections(slotValues) {
    const seen = new Set();
    for (let i = 0; i < slotValues.length; i++) {
      if (slotValues[i] === "") continue;
      const q = quartzList[parseInt(slotValues[i], 10)];
      if (!q) {
        slotValues[i] = "";
        continue;
      }
      if (quartzAllowsDuplicateAcrossSlots(q)) continue;
      const t = Number(q.type);
      if (seen.has(t)) slotValues[i] = "";
      else seen.add(t);
    }
  }

  function updateQuartzEffectCells() {
    const char = getSelectedCharacter();
    if (!char) return;
    char.orbment.forEach(function (_slot, i) {
      const td = document.getElementById("quartz-effect-" + i);
      const sel = document.getElementById("quartz-slot-" + i);
      if (!td || !sel) return;
      const v = sel.value;
      if (v === "") {
        td.textContent = "—";
        td.className = "quartz-effect-cell muted";
        return;
      }
      const q = quartzList[parseInt(v, 10)];
      td.textContent = q && q.effect != null && String(q.effect).trim() !== "" ? q.effect : "—";
      td.className = "quartz-effect-cell";
    });
  }

  function refreshAllQuartzSelects() {
    const char = getSelectedCharacter();
    if (!char) return;

    const n = char.orbment.length;
    const vals = [];
    for (let i = 0; i < n; i++) {
      const sel = document.getElementById("quartz-slot-" + i);
      vals[i] = sel ? sel.value : "";
    }
    resolveConflictingSelections(vals);

    for (let i = 0; i < n; i++) {
      const usedTypes = usedTypesExceptSlot(i, vals);
      const sel = document.getElementById("quartz-slot-" + i);
      if (!sel) continue;
      const slot = char.orbment[i];
      const cur = vals[i];

      sel.innerHTML = "";
      const optNone = document.createElement("option");
      optNone.value = "";
      optNone.textContent = "— None —";
      optNone.className = "quartz-option neutral";
      sel.appendChild(optNone);

      quartzList.forEach(function (q, idx) {
        if (!(slot.elemental == null || q.elemental === slot.elemental)) return;
        if (cur !== String(idx) && usedTypes.has(Number(q.type))) return;
        const opt = document.createElement("option");
        opt.value = String(idx);
        opt.textContent = q.name;
        opt.className = "quartz-option " + elementalClass(q.elemental);
        if (q.effect) opt.title = q.effect;
        sel.appendChild(opt);
      });

      if (cur !== "" && !Array.prototype.some.call(sel.options, function (o) { return o.value === cur; })) {
        sel.value = "";
        vals[i] = "";
      } else {
        sel.value = cur;
      }
    }

    updateQuartzEffectCells();
    recalcLineTotals();
  }

  function getSelectedCharacter() {
    const name = characterSelect.value;
    if (!name) return null;
    return characters.find(function (c) {
      return c.name === name;
    }) || null;
  }

  /** Sepith totals per positive line + aggregate when no positive lines (same rules as line table). */
  function computeLineSepithTotals(char) {
    const positiveLines = distinctPositiveLines(char.orbment);
    const totals = {};
    positiveLines.forEach(function (L) {
      totals[L] = zeroRow();
    });
    const aggregate = zeroRow();

    char.orbment.forEach(function (slot, i) {
      const sel = document.getElementById("quartz-slot-" + i);
      if (!sel) return;
      const v = sel.value;
      if (v === "") return;
      const Q = quartzList[parseInt(v, 10)];
      if (!Q || !Q.cost) return;

      const L = slot.line;
      function addCost(target) {
        ELEMENTS.forEach(function (e) {
          target[e] += Number(Q.cost[e]) || 0;
        });
      }

      if (L > 0) {
        if (totals[L]) addCost(totals[L]);
      } else {
        if (positiveLines.length) {
          positiveLines.forEach(function (ln) {
            addCost(totals[ln]);
          });
        } else {
          addCost(aggregate);
        }
      }
    });

    return { positiveLines: positiveLines, totals: totals, aggregate: aggregate };
  }

  function rowMeetsElementalRequirement(row, req) {
    if (!req) return true;
    return ELEMENTS.every(function (e) {
      return Number(row[e]) >= (Number(req[e]) || 0);
    });
  }

  function summarizeElementalValue(ev) {
    if (!ev) return "—";
    const parts = [];
    ELEMENTS.forEach(function (e) {
      const n = Number(ev[e]) || 0;
      if (n > 0) parts.push(e + " ×" + n);
    });
    return parts.length ? parts.join(", ") : "—";
  }

  function summarizeTime(t) {
    if (!t || typeof t !== "object") return "—";
    const c = t.cast != null ? t.cast : "—";
    const d = t.delay != null ? t.delay : "—";
    return "Cast " + c + " AT / Delay " + d + " AT";
  }

  /** Line numbers on which current sepith totals meet the art's elemental-value. */
  function enablingLinesForArt(art, positiveLines, totals, aggregate) {
    const req = art["elemental-value"];
    const lines = [];
    positiveLines.forEach(function (L) {
      if (rowMeetsElementalRequirement(totals[L], req)) lines.push(L);
    });
    if (positiveLines.length === 0 && rowMeetsElementalRequirement(aggregate, req)) {
      lines.push(0);
    }
    return lines;
  }

  function renderEnabledArtsTable(char, positiveLines, totals, aggregate) {
    artsBody.innerHTML = "";
    if (!char || !Array.isArray(artsList) || artsList.length === 0) {
      artsEmptyMsg.classList.remove("hidden");
      artsEmptyMsg.textContent = "No arts data for this game.";
      return;
    }

    const rows = [];
    artsList.forEach(function (art) {
      const lines = enablingLinesForArt(art, positiveLines, totals, aggregate);
      if (lines.length === 0) return;
      rows.push({ art: art, lines: lines });
    });

    rows.sort(function (a, b) {
      return a.art.name.localeCompare(b.art.name);
    });

    rows.forEach(function (item) {
      const art = item.art;
      const tr = document.createElement("tr");

      const tdName = document.createElement("td");
      const strong = document.createElement("div");
      strong.className = "art-name";
      strong.textContent = art.name || "—";
      tdName.appendChild(strong);
      if (art.description) {
        const desc = document.createElement("div");
        desc.className = "art-desc";
        desc.textContent = art.description;
        tdName.appendChild(desc);
      }
      tr.appendChild(tdName);

      const tdLines = document.createElement("td");
      tdLines.className = "col-lines";
      tdLines.textContent = item.lines.join(", ");
      tr.appendChild(tdLines);

      const tdEl = document.createElement("td");
      tdEl.textContent = art.elemental != null ? String(art.elemental) : "—";
      tr.appendChild(tdEl);

      const tdEv = document.createElement("td");
      tdEv.className = "col-elemental-value";
      tdEv.textContent = summarizeElementalValue(art["elemental-value"]);
      tr.appendChild(tdEv);

      const tdCost = document.createElement("td");
      tdCost.textContent = art.cost != null ? String(art.cost) : "—";
      tr.appendChild(tdCost);

      const tdTime = document.createElement("td");
      tdTime.textContent = summarizeTime(art.time);
      tr.appendChild(tdTime);

      const tdPow = document.createElement("td");
      tdPow.textContent = art.power != null ? String(art.power) : "—";
      tr.appendChild(tdPow);

      const tdTg = document.createElement("td");
      tdTg.className = "col-target";
      tdTg.textContent = art["target-effect"] != null ? String(art["target-effect"]) : "—";
      tr.appendChild(tdTg);

      artsBody.appendChild(tr);
    });

    if (rows.length === 0) {
      artsEmptyMsg.classList.remove("hidden");
      artsEmptyMsg.textContent = "No arts match current sepith on any line.";
    } else {
      artsEmptyMsg.classList.add("hidden");
    }
  }

  function recalcLineTotals() {
    const char = getSelectedCharacter();
    lineBody.innerHTML = "";
    artsBody.innerHTML = "";
    if (!char) {
      artsEmptyMsg.classList.add("hidden");
      return;
    }

    const data = computeLineSepithTotals(char);
    const positiveLines = data.positiveLines;
    const totals = data.totals;
    const aggregate = data.aggregate;

    lineEmptyMsg.classList.add("hidden");
    if (positiveLines.length) {
      positiveLines.forEach(function (L) {
        const tr = document.createElement("tr");
        const lineBg = quartzLineClass(L);
        if (lineBg) tr.className = lineBg;
        const t0 = document.createElement("td");
        t0.textContent = String(L);
        tr.appendChild(t0);
        ELEMENTS.forEach(function (e) {
          const td = document.createElement("td");
          td.textContent = String(totals[L][e]);
          tr.appendChild(td);
        });
        lineBody.appendChild(tr);
      });
    } else {
      const tr = document.createElement("tr");
      const label = document.createElement("td");
      label.textContent = "0";
      label.title = "All lines (no positive line groups)";
      tr.appendChild(label);
      ELEMENTS.forEach(function (e) {
        const td = document.createElement("td");
        td.textContent = String(aggregate[e]);
        tr.appendChild(td);
      });
      lineBody.appendChild(tr);
    }

    renderEnabledArtsTable(char, positiveLines, totals, aggregate);
  }

  function renderCharacterUi() {
    slotsBody.innerHTML = "";
    lineBody.innerHTML = "";
    const char = getSelectedCharacter();
    if (!char) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");

    char.orbment.forEach(function (slot, i) {
      const tr = document.createElement("tr");

      const tdEl = document.createElement("td");
      tdEl.className = "elemental-cell " + elementalClass(slot.elemental);
      if (slot.elemental == null) tdEl.textContent = "—";
      else tdEl.textContent = slot.elemental;
      tr.appendChild(tdEl);

      const tdQz = document.createElement("td");
      const qzLine = quartzLineClass(slot.line);
      if (qzLine) tdQz.className = qzLine;
      const sel = document.createElement("select");
      sel.id = "quartz-slot-" + i;
      sel.setAttribute("aria-label", "Quartz for slot " + (i + 1));

      const optNone = document.createElement("option");
      optNone.value = "";
      optNone.textContent = "— None —";
      sel.appendChild(optNone);

      sel.addEventListener("change", refreshAllQuartzSelects);
      tdQz.appendChild(sel);
      tr.appendChild(tdQz);

      const tdEffect = document.createElement("td");
      tdEffect.id = "quartz-effect-" + i;
      tdEffect.className = "quartz-effect-cell muted";
      tdEffect.textContent = "—";
      tr.appendChild(tdEffect);

      slotsBody.appendChild(tr);
    });

    refreshAllQuartzSelects();
  }

  async function onGameChange() {
    clearError();
    characterSelect.innerHTML = "";

    const g = gameSelect.value;
    if (!g) {
      characterSelect.disabled = true;
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "Select a game first…";
      characterSelect.appendChild(o);
      characters = [];
      quartzList = [];
      artsList = [];
      panel.classList.add("hidden");
      return;
    }

    characterSelect.disabled = true;
    characters = [];
    quartzList = [];
    artsList = [];

    try {
      const [cr, qr, ar] = await Promise.all([
        fetch("games/" + g + "/characters.json"),
        fetch("games/" + g + "/quartz.json"),
        fetch("games/" + g + "/arts.json"),
      ]);
      if (!cr.ok) throw new Error("characters.json: " + cr.status);
      if (!qr.ok) throw new Error("quartz.json: " + qr.status);
      characters = await cr.json();
      quartzList = await qr.json();
      if (ar.ok) {
        artsList = await ar.json();
        if (!Array.isArray(artsList)) artsList = [];
      } else {
        artsList = [];
      }
    } catch (e) {
      showError("Could not load data: " + (e && e.message ? e.message : String(e)));
      characterSelect.disabled = true;
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "Load failed";
      characterSelect.appendChild(o);
      panel.classList.add("hidden");
      return;
    }

    if (!Array.isArray(characters) || characters.length === 0) {
      characterSelect.disabled = true;
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "No characters";
      characterSelect.appendChild(o);
      panel.classList.add("hidden");
      return;
    }

    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "Select a character…";
    characterSelect.appendChild(opt0);

    characters.forEach(function (c) {
      const o = document.createElement("option");
      o.value = c.name;
      o.textContent = c.name;
      characterSelect.appendChild(o);
    });
    characterSelect.disabled = false;
    characterSelect.value = "";
    panel.classList.add("hidden");
  }

  gameSelect.addEventListener("change", onGameChange);
  characterSelect.addEventListener("change", function () {
    renderCharacterUi();
  });
})();
