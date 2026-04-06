const API_BASE = "http://127.0.0.1:8000";

let currentEpisodeId = null;
let historyLog = [];

const startBtn = document.getElementById("startBtn");
const submitBtn = document.getElementById("submitBtn");

const taskTypeEl = document.getElementById("taskType");
const difficultyEl = document.getElementById("difficulty");
const episodeIdText = document.getElementById("episodeIdText");

const observationBox = document.getElementById("observationBox");
const resultBox = document.getElementById("resultBox");
const historyBox = document.getElementById("historyBox");

const summaryEl = document.getElementById("summary");
const strategiesEl = document.getElementById("strategies");
const selfScoreEl = document.getElementById("selfScore");
const notesEl = document.getElementById("notes");

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function updateHistory() {
  if (historyLog.length === 0) {
    historyBox.textContent = "No history yet.";
    return;
  }

  historyBox.textContent = historyLog
    .map((item, idx) => `Step ${idx + 1}\n${pretty(item)}`)
    .join("\n\n-----------------------------\n\n");
}

function getScheduleBlocks() {
  const blocks = [
    {
      start: document.getElementById("start1").value.trim(),
      end: document.getElementById("end1").value.trim(),
      activity: document.getElementById("activity1").value.trim(),
      priority: document.getElementById("priority1").value,
      rationale: document.getElementById("rationale1").value.trim()
    },
    {
      start: document.getElementById("start2").value.trim(),
      end: document.getElementById("end2").value.trim(),
      activity: document.getElementById("activity2").value.trim(),
      priority: document.getElementById("priority2").value,
      rationale: document.getElementById("rationale2").value.trim()
    }
  ];

  return blocks.filter(
    block => block.start && block.end && block.activity
  );
}

startBtn.addEventListener("click", async () => {
  try {
    const payload = {
      task_type: taskTypeEl.value || null,
      difficulty: difficultyEl.value || null
    };

    const res = await fetch(`${API_BASE}/reset`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Reset failed: ${res.status}`);
    }

    const data = await res.json();

    currentEpisodeId = data.episode_id;
    episodeIdText.textContent = `Episode ID: ${currentEpisodeId}`;
    observationBox.textContent = pretty(data.observation);
    resultBox.textContent = "Episode started. Submit a plan.";
    historyLog = [];
    updateHistory();
  } catch (err) {
    resultBox.textContent = `Error: ${err.message}`;
  }
});

submitBtn.addEventListener("click", async () => {
  if (!currentEpisodeId) {
    alert("Start an episode first.");
    return;
  }

  const scheduleBlocks = getScheduleBlocks();

  if (scheduleBlocks.length < 2) {
    alert("You must provide at least 2 valid schedule blocks.");
    return;
  }

  try {
    const payload = {
      episode_id: currentEpisodeId,
      action: {
        summary: summaryEl.value.trim(),
        schedule: scheduleBlocks,
        strategies: strategiesEl.value
          .split(",")
          .map(s => s.trim())
          .filter(Boolean),
        self_score: parseFloat(selfScoreEl.value),
        notes: notesEl.value.trim()
      }
    };

    const res = await fetch(`${API_BASE}/step`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Step failed: ${res.status}\n${errorText}`);
    }

    const data = await res.json();

    observationBox.textContent = pretty(data.observation);
    resultBox.textContent = pretty({
      reward: data.reward,
      done: data.done,
      info: data.info
    });

    historyLog.push({
      action: payload.action,
      result: data
    });

    updateHistory();

    if (data.done) {
      currentEpisodeId = null;
      episodeIdText.textContent += " (Completed)";
    }
  } catch (err) {
    resultBox.textContent = `Error: ${err.message}`;
  }
});