"use strict";
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const stageName = (s) => (s === "objective" ? "客观题练习" : "主观题训练");
const state = {
  code: "",
  user: null,
  stage: "objective",
  subject: "",
  subjects: [],
  rows: [],
  scope: "all",
  q: null,
  busy: false,
  selected: [],
  records: {},
  stars: [],
  drafts: {},
  last: null,
  completed: false,
};
let storageFailed = false;
function toast(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => ($("toast").hidden = true), 4000);
}
function key() {
  return "fakao:v2:" + state.user.id;
}
function save() {
  try {
    localStorage.setItem(
      key(),
      JSON.stringify({
        records: state.records,
        stars: state.stars,
        drafts: state.drafts,
        last: state.last,
      }),
    );
  } catch (e) {
    if (!storageFailed) {
      storageFailed = true;
      toast("浏览器无法保存记录，请保留当前页面");
    }
  }
}
function restore() {
  let data = {};
  try {
    data = JSON.parse(localStorage.getItem(key()) || "{}") || {};
  } catch (e) {
    toast("本机记录无法读取，已开启新练习");
  }
  state.records = data.records || {};
  state.stars = Array.isArray(data.stars) ? data.stars : [];
  state.drafts = data.drafts || {};
  state.last = data.last || null;
}
function qkey(q = state.q) {
  return JSON.stringify([state.stage, state.subject, q.question_id]);
}
function showPage(page) {
  for (const name of ["gate", "lobby", "practice"])
    $(name).hidden = name !== page;
}
async function api(path, body) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: {
      "X-Access-Code": state.code,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let data = {};
    try {
      data = await response.json();
    } catch {}
    throw Error(
      typeof data.detail === "string" ? data.detail : "请求暂时失败，请重试",
    );
  }
  return response.json();
}
function setBusy(value) {
  state.busy = value;
  document
    .querySelectorAll(
      "#account button,#scopeTabs button,#filters button,.filters select,#questionCard button,#options input,#answer",
    )
    .forEach((el) => (el.disabled = value));
}
$("loginForm").onsubmit = async (e) => {
  e.preventDefault();
  $("loginError").textContent = "";
  $("loginBtn").disabled = true;
  try {
    state.code = $("code").value.trim();
    const data = await api("/api/verify", { code: state.code });
    state.user = data.user;
    state.subjects = (await api("/api/subjects")).subjects;
    restore();
    $("account").hidden = false;
    $("headerNote").hidden = true;
    $("userBtn").textContent = state.user.name + " · 切换";
    showLobby();
  } catch (err) {
    $("loginError").textContent = err.message;
  } finally {
    $("loginBtn").disabled = false;
  }
};
function showLobby() {
  if (state.busy) return;
  showPage("lobby");
  $("resumeBtn").hidden = !state.last;
  renderSubjects();
}
$("homeBtn").onclick = showLobby;
$("userBtn").onclick = () => {
  if (state.busy) return;
  state.code = "";
  state.user = null;
  state.q = null;
  state.rows = [];
  state.records = {};
  state.stars = [];
  state.drafts = {};
  state.last = null;
  $("code").value = "";
  $("answer").value = "";
  $("result").innerHTML = "";
  $("account").hidden = true;
  $("headerNote").hidden = false;
  showPage("gate");
  $("code").focus();
};
$("stageTabs").onclick = (e) => {
  const b = e.target.closest("[data-stage]");
  if (b) {
    state.stage = b.dataset.stage;
    renderSubjects();
  }
};
function renderSubjects() {
  document.querySelectorAll("[data-stage]").forEach((b) => {
    b.classList.toggle("active", b.dataset.stage === state.stage);
    b.setAttribute("aria-pressed", String(b.dataset.stage === state.stage));
  });
  const rows = state.subjects.filter((x) => x.stage === state.stage);
  $("stageCount").textContent =
    rows.reduce((s, x) => s + x.practice_count, 0) + " 道可练习题目";
  $("subjectGrid").innerHTML = rows
    .map(
      (s) =>
        `<button class="subject-card" data-subject="${esc(s.subject)}"><strong>${esc(s.subject)}</strong><span class="arrow">↗</span><small>${s.practice_count} 道可练习 · ${s.count} 道资料</small><small>${state.stage === "objective" ? "作答后查看答案与解析" : `${s.scored_count} 道参考试评 · 其余提供建议`}</small></button>`,
    )
    .join("");
}
$("subjectGrid").onclick = (e) => {
  const b = e.target.closest("[data-subject]");
  if (b) enter(state.stage, b.dataset.subject);
};
$("resumeBtn").onclick = () => {
  if (state.last)
    enter(state.last.stage, state.last.subject, state.last.question_id);
};
async function enter(stage, subject, resume) {
  if (state.busy) return;
  state.stage = stage;
  state.subject = subject;
  state.scope = "all";
  $("knowledge").value = "";
  $("result").hidden = true;
  $("questionCard").hidden = true;
  showPage("practice");
  $("practiceTitle").textContent = subject;
  $("breadcrumb").textContent = stageName(stage);
  $("empty").hidden = false;
  $("emptyTitle").textContent = "正在准备题目…";
  $("emptyText").textContent = "";
  setBusy(true);
  try {
    const data = await api(
      "/api/questions?" +
        new URLSearchParams({ stage, subject, mode: "browse", limit: 1500 }),
    );
    state.rows = data.items;
    const points = [
      ...new Set(state.rows.flatMap((q) => q.knowledge_points || [])),
    ].sort();
    $("knowledge").innerHTML =
      '<option value="">全部知识点</option>' +
      points
        .map((p) => `<option value="${esc(p)}">${esc(p)}</option>`)
        .join("");
    if (
      resume &&
      state.rows.find((q) => q.question_id === resume && !q.practice_ready)
    )
      state.scope = "browse";
    updateTabs();
    updateStats();
    pick(resume);
  } catch (e) {
    $("emptyTitle").textContent = "题目加载失败";
    $("emptyText").textContent = e.message;
  } finally {
    setBusy(false);
  }
}
function currentRows() {
  return state.rows.filter(
    (q) =>
      (!$("knowledge").value ||
        (q.knowledge_points || []).includes($("knowledge").value)) &&
      (state.scope === "browse" || q.practice_ready) &&
      (state.scope !== "stars" || state.stars.includes(qkey(q))) &&
      (state.scope !== "wrong" || state.records[qkey(q)]?.wrong),
  );
}
function updateTabs() {
  const wrong = state.rows.filter((q) => state.records[qkey(q)]?.wrong).length;
  const stars = state.rows.filter((q) => state.stars.includes(qkey(q))).length;
  document.querySelectorAll("[data-scope]").forEach((b) => {
    b.classList.toggle("active", b.dataset.scope === state.scope);
    b.setAttribute("aria-pressed", String(b.dataset.scope === state.scope));
    b.textContent = {
      all: "全部练习",
      wrong: "错题重练 " + wrong,
      stars: "我的收藏 " + stars,
      browse: "资料浏览",
    }[b.dataset.scope];
  });
}
$("scopeTabs").onclick = (e) => {
  const b = e.target.closest("[data-scope]");
  if (b && !state.busy) {
    state.scope = b.dataset.scope;
    updateTabs();
    pick();
  }
};
$("resetScope").onclick = () => {
  if (!state.rows.length) {
    enter(state.stage, state.subject);
    return;
  }
  state.scope = "all";
  $("knowledge").value = "";
  updateTabs();
  pick();
};
$("knowledge").onchange = () => pick();
function pick(resume) {
  const rows = currentRows();
  $("result").hidden = true;
  $("empty").hidden = !!rows.length;
  $("questionCard").hidden = !rows.length;
  if (!rows.length) {
    state.q = null;
    $("position").textContent = "0 道";
    $("emptyTitle").textContent = {
      wrong: "暂时没有待巩固题目",
      stars: "还没有收藏题目",
      all: "当前条件下暂无可练题目",
      browse: "暂无匹配资料",
    }[state.scope];
    $("emptyText").textContent =
      state.scope === "wrong"
        ? "完成练习后，需要巩固的题目会出现在这里。"
        : "可以调整知识点筛选，或返回全部练习。";
    return;
  }
  let index = resume ? rows.findIndex((q) => q.question_id === resume) : -1;
  if (index < 0) {
    if ($("order").value === "random") {
      const choices = rows.filter(
        (q) => q.question_id !== state.q?.question_id,
      );
      const selected = (choices.length ? choices : rows)[
        Math.floor(Math.random() * (choices.length || rows.length))
      ];
      index = rows.indexOf(selected);
    } else {
      index =
        (rows.findIndex((q) => q.question_id === state.q?.question_id) + 1) %
        rows.length;
    }
  }
  state.q = rows[index];
  state.completed = false;
  state.selected = [];
  state.last = {
    stage: state.stage,
    subject: state.subject,
    question_id: state.q.question_id,
  };
  save();
  renderQuestion(index, rows.length);
}
function renderQuestion(index, total) {
  const q = state.q;
  const draft = state.drafts[qkey()] || {};
  state.selected = Array.isArray(draft.selected) ? draft.selected : [];
  $("position").textContent = `${index + 1} / ${total} 道`;
  $("typeBadge").textContent = q.type_label;
  $("qNumber").textContent = q.foundation ? "基础巩固" : "专项练习";
  $("stem").textContent = q.stem;
  $("foundation").hidden = !q.foundation;
  $("foundation").textContent =
    state.stage === "subjective"
      ? "主客共用 · 基础训练资料"
      : "判断题用于基础巩固";
  $("sourceInfo").textContent =
    `来源：${q.source_id || "待补充"}${q.source_page ? " · 第 " + q.source_page + " 页" : ""}`;
  $("workarea").classList.toggle("split", state.stage === "subjective");
  $("textAnswer").hidden = state.stage !== "subjective";
  $("options").hidden = state.stage !== "objective";
  $("answer").value = draft.answer || "";
  $("wordCount").textContent = $("answer").value.length + " 字";
  $("draftState").textContent = draft.answer
    ? "已恢复上次草稿"
    : "草稿自动保存在本机";
  $("gradingMode").textContent = q.can_score
    ? "按依据参考试评"
    : "分析建议 · 不计分";
  $("options").innerHTML = (q.options || [])
    .map(
      (o) =>
        `<label class="option"><input type="${q.question_type === "multiple_choice" ? "checkbox" : "radio"}" name="option" value="${esc(o.key)}" ${state.selected.includes(o.key) ? "checked" : ""}><b>${esc(o.key)}</b><span>${esc(o.text)}</span></label>`,
    )
    .join("");
  $("submitBtn").hidden = !q.practice_ready;
  $("submitBtn").textContent =
    state.stage === "objective"
      ? "提交答案"
      : q.can_score
        ? "提交参考试评"
        : "获取分析建议";
  $("unavailable").hidden = q.practice_ready;
  $("unavailable").textContent = q.unavailable_reason;
  renderHistory();
  renderStar();
}
function renderHistory() {
  const r = state.records[qkey()];
  $("reviewBtn").hidden = state.stage !== "subjective";
  $("reviewBtn").textContent = r?.wrong
    ? "已标记待巩固 · 点击移除"
    : "标记为待巩固";
  $("past").hidden = !r?.attempts.length;
  $("pastItems").innerHTML = (r?.attempts || [])
    .slice()
    .reverse()
    .map(
      (a) =>
        `<div class="point"><p class="fine">${esc(new Date(a.at).toLocaleString())}</p><p>${esc(a.answer)}</p><p>${esc(a.feedback?.summary || (a.correct === true ? "答对" : a.correct === false ? "待巩固" : ""))}</p>${(a.feedback?.points || []).map(pointHTML).join("")}</div>`,
    )
    .join("");
  $("history").textContent = r?.attempts.length
    ? `已练 ${r.attempts.length} 次 · ${state.stage === "objective" ? (r.attempts.at(-1).correct ? "上次答对" : "上次待巩固") : r.best != null ? "最高参考得分 " + r.best + "%" : "已获得分析建议"}`
    : "首次练习，按自己的理解作答";
}
$("reviewBtn").onclick = () => {
  const k = qkey();
  const r = state.records[k] || { attempts: [], best: null, wrong: false };
  r.wrong = !r.wrong;
  state.records[k] = r;
  save();
  renderHistory();
  updateStats();
  updateTabs();
};
function renderStar() {
  const on = state.stars.includes(qkey());
  $("starBtn").textContent = on ? "★ 已收藏" : "☆ 收藏";
  $("starBtn").setAttribute("aria-pressed", String(on));
}
$("starBtn").onclick = () => {
  const k = qkey();
  state.stars = state.stars.includes(k)
    ? state.stars.filter((x) => x !== k)
    : [...state.stars, k];
  save();
  renderStar();
  updateTabs();
};
function saveDraft() {
  if (!state.q) return;
  state.drafts[qkey()] = {
    answer: $("answer").value,
    selected: state.selected,
  };
  save();
}
$("answer").oninput = () => {
  state.completed = false;
  saveDraft();
  $("draftState").textContent = storageFailed
    ? "暂时无法保存，请保留页面"
    : "草稿已保存";
  $("wordCount").textContent = $("answer").value.length + " 字";
};
$("options").onchange = () => {
  state.completed = false;
  state.selected = [...document.querySelectorAll("#options input:checked")].map(
    (x) => x.value,
  );
  saveDraft();
};
$("nextBtn").onclick = () => {
  if (!state.busy) {
    pick();
    $("questionCard").scrollIntoView({ behavior: "smooth", block: "start" });
  }
};
function referenceHTML(r) {
  return `<h3>参考答案</h3><p>${esc(r.answer)}</p><h3>解析</h3><p>${esc(r.explanation)}</p><p class="fine">${esc(r.review_note)}</p>`;
}
$("peekBtn").onclick = async () => {
  if (state.busy) return;
  setBusy(true);
  try {
    const r = await api(
      "/api/questions/" +
        encodeURIComponent(state.q.question_id) +
        "/reference",
    );
    $("result").hidden = false;
    $("result").innerHTML =
      '<h2>参考答案与解析</h2><p class="muted">本次查看不计入完成次数。</p>' +
      referenceHTML(r);
  } catch (e) {
    toast(e.message);
  } finally {
    setBusy(false);
  }
};
function dayKey() {
  const d = new Date();
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, "0"),
    String(d.getDate()).padStart(2, "0"),
  ].join("-");
}
function record(result) {
  const k = qkey(),
    r = state.records[k] || { attempts: [], best: null, wrong: false };
  const percent =
    result.score != null && result.max_score
      ? Math.round((result.score / result.max_score) * 100)
      : null;
  r.attempts.push({
    day: dayKey(),
    at: Date.now(),
    correct: result.correct,
    percent,
    answer:
      state.stage === "subjective"
        ? $("answer").value
        : state.selected.join(","),
    feedback: result,
  });
  r.wrong =
    state.stage === "objective"
      ? !result.correct
      : percent != null
        ? percent < 100
        : r.wrong;
  if (percent != null) r.best = Math.max(r.best ?? 0, percent);
  state.records[k] = r;
  delete state.drafts[k];
  state.completed = true;
  save();
  updateStats();
  updateTabs();
  renderHistory();
  $("draftState").textContent = "本次作答与反馈已保存";
}
function updateStats() {
  const records = state.rows.map((q) => state.records[qkey(q)]).filter(Boolean),
    today = records
      .flatMap((r) => r.attempts)
      .filter((a) => a.day === dayKey());
  let scored = today.filter((a) =>
    state.stage === "objective"
      ? typeof a.correct === "boolean"
      : a.percent != null,
  );
  let metric = scored.length
    ? Math.round(
        scored.reduce(
          (s, a) =>
            s +
            (state.stage === "objective" ? (a.correct ? 100 : 0) : a.percent),
          0,
        ) / scored.length,
      ) + "%"
    : "—";
  $("stats").innerHTML = [
    [today.length, "今日完成"],
    [metric, state.stage === "objective" ? "今日正确率" : "参考得分率"],
    [records.filter((r) => r.wrong).length, "待巩固"],
    [
      state.rows.filter((q) => state.stars.includes(qkey(q))).length,
      "收藏题目",
    ],
  ]
    .map(([n, label]) => `<div class="stat"><b>${n}</b>${label}</div>`)
    .join("");
}
function pointHTML(p) {
  return `<div class="point"><strong class="${p.status === "hit" ? "good" : "bad"}">${p.status === "hit" ? "已命中" : "待完善"} · ${esc(p.standard)}</strong><span class="muted"> ${p.score} / ${p.max_score} 分</span>${p.evidence ? `<blockquote>你的作答：${esc(p.evidence)}</blockquote>` : ""}<p>${esc(p.suggestion)}</p></div>`;
}
async function streamGrade() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 110000);
  let complete = null;
  try {
    const response = await fetch("/api/grade_stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Access-Code": state.code,
      },
      body: JSON.stringify({
        question_id: state.q.question_id,
        answer: $("answer").value,
      }),
      signal: controller.signal,
    });
    if (!response.ok) throw Error("批改服务暂时不可用");
    const reader = response.body.getReader(),
      decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let end;
      while ((end = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        const kind = block
          .split("\n")
          .find((l) => l.startsWith("event: "))
          ?.slice(7);
        const data = block
          .split("\n")
          .filter((l) => l.startsWith("data: "))
          .map((l) => l.slice(6))
          .join("\n");
        if (!data) continue;
        const payload = JSON.parse(data);
        if (kind === "error") throw Error(payload.message);
        if (kind === "point")
          $("result").insertAdjacentHTML("beforeend", pointHTML(payload));
        if (kind === "complete") complete = payload;
      }
    }
    if (!complete) throw Error("连接中断，作答已保留，请重新提交");
    return complete;
  } finally {
    clearTimeout(timer);
    controller.abort();
  }
}
$("submitBtn").onclick = async () => {
  if (state.busy || !state.q) return;
  if (state.completed) {
    toast("本次作答已记录。修改答案后可重新提交。");
    return;
  }
  if (state.stage === "objective" && !state.selected.length) {
    toast("请先选择答案");
    return;
  }
  if (state.stage === "subjective" && !$("answer").value.trim()) {
    toast("请先填写你的作答");
    $("answer").focus();
    return;
  }
  saveDraft();
  setBusy(true);
  $("result").hidden = false;
  $("result").innerHTML =
    '<p class="loading">' +
    (state.stage === "objective"
      ? "正在核对答案…"
      : "正在核对作答与参考依据，通常需要片刻…") +
    "</p>";
  try {
    let r;
    if (state.stage === "objective") {
      r = await api("/api/submit", {
        question_id: state.q.question_id,
        selected: state.selected,
      });
      $("result").innerHTML =
        `<h2 class="${r.correct ? "good" : "bad"}">${r.correct ? "回答正确，继续保持" : "这道题，再巩固一下"}</h2><p>你的选择：${esc(r.selected.join("、"))}　参考答案：${esc(r.answer_keys.join("、"))}</p>` +
        referenceHTML(r);
    } else {
      r = await streamGrade();
      $("result").innerHTML =
        `<h2>${r.score != null ? `<span class="score">${r.score}</span> / ${r.max_score} 分 · 参考试评` : "本次作答反馈"}</h2><p class="notice">${esc(r.scoring_note)}</p><p>${esc(r.summary)}</p>${r.points.map(pointHTML).join("")}<h3>下一次可以这样改进</h3><p>${esc(r.suggestions)}</p><details><summary>展开参考答案与解析</summary>${referenceHTML(r.reference)}</details>`;
    }
    record(r);
  } catch (e) {
    $("result").innerHTML =
      `<h2>作答已保留</h2><p class="error">${esc(e.name === "AbortError" ? "批改超时，请重试" : e.message)}</p><p class="muted">本次未计入完成记录。可以继续编辑，再次提交。</p>`;
  } finally {
    setBusy(false);
  }
};
