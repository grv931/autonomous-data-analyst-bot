DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autonomous Data Analyst Agent | Telemetry Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { background-color: #0b0f19; font-family: system-ui, -apple-system, sans-serif; color: #e2e8f0; }
    .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .card-glow:hover { border-color: rgba(99, 102, 241, 0.4); box-shadow: 0 0 20px rgba(99, 102, 241, 0.15); transition: all 0.3s; }
  </style>
</head>
<body class="min-h-screen p-4 sm:p-8">
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-gray-800">
      <div>
        <div class="flex items-center gap-3">
          <div class="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
            <i class="fa-solid fa-brain text-2xl"></i>
          </div>
          <div>
            <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
              Autonomous Data Analyst Agent
            </h1>
            <p class="text-xs text-gray-400">Live Agent Telemetry, Audit Logs & Diagnostic Monitor</p>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Service Operational
        </span>
        <a href="/run.jsonl" download class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 transition">
          <i class="fa-solid fa-download"></i> Raw run.jsonl
        </a>
      </div>
    </header>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" id="statsGrid">
      <div class="glass p-5 rounded-xl card-glow">
        <div class="flex justify-between items-center text-gray-400 text-xs font-medium uppercase tracking-wider">
          <span>Total Invocations</span>
          <i class="fa-solid fa-bolt text-indigo-400"></i>
        </div>
        <div class="mt-2 text-3xl font-bold text-white" id="statQueries">--</div>
        <p class="text-xs text-gray-500 mt-1">Audit events recorded</p>
      </div>

      <div class="glass p-5 rounded-xl card-glow">
        <div class="flex justify-between items-center text-gray-400 text-xs font-medium uppercase tracking-wider">
          <span>Success Rate</span>
          <i class="fa-solid fa-check-circle text-emerald-400"></i>
        </div>
        <div class="mt-2 text-3xl font-bold text-emerald-400" id="statSuccess">--%</div>
        <p class="text-xs text-gray-500 mt-1">Autonomous self-healed</p>
      </div>

      <div class="glass p-5 rounded-xl card-glow">
        <div class="flex justify-between items-center text-gray-400 text-xs font-medium uppercase tracking-wider">
          <span>Avg Latency</span>
          <i class="fa-solid fa-stopwatch text-amber-400"></i>
        </div>
        <div class="mt-2 text-3xl font-bold text-amber-400" id="statLatency">-- ms</div>
        <p class="text-xs text-gray-500 mt-1">End-to-end processing</p>
      </div>

      <div class="glass p-5 rounded-xl card-glow">
        <div class="flex justify-between items-center text-gray-400 text-xs font-medium uppercase tracking-wider">
          <span>Visualizations</span>
          <i class="fa-solid fa-chart-pie text-purple-400"></i>
        </div>
        <div class="mt-2 text-3xl font-bold text-purple-400" id="statCharts">--</div>
        <p class="text-xs text-gray-500 mt-1">Plots rendered via sandbox</p>
      </div>
    </div>

    <!-- Live Event Log Table -->
    <div class="glass rounded-xl overflow-hidden border border-gray-800">
      <div class="p-4 border-b border-gray-800 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-list-check text-indigo-400"></i>
          <h2 class="text-sm font-semibold text-gray-200">Recent Audit Interactions (run.jsonl)</h2>
        </div>
        <span class="text-xs text-gray-500">Auto-refreshes every 5s</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-gray-900/60 text-gray-400 font-semibold border-b border-gray-800 uppercase tracking-wider">
            <tr>
              <th class="p-3">Timestamp</th>
              <th class="p-3">Chat ID</th>
              <th class="p-3">User Query</th>
              <th class="p-3">Code Executed</th>
              <th class="p-3">Result / Answer</th>
              <th class="p-3">Latency</th>
              <th class="p-3">Status</th>
            </tr>
          </thead>
          <tbody id="logsTableBody" class="divide-y divide-gray-800/60 font-mono text-gray-300">
            <tr>
              <td colspan="7" class="p-6 text-center text-gray-500">Awaiting incoming queries...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    async function updateTelemetry() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        
        document.getElementById('statQueries').textContent = data.stats.total_queries;
        document.getElementById('statSuccess').textContent = data.stats.success_rate + '%';
        document.getElementById('statLatency').textContent = data.stats.avg_latency_ms + ' ms';
        document.getElementById('statCharts').textContent = data.stats.charts_generated;

        const tbody = document.getElementById('logsTableBody');
        if (data.logs && data.logs.length > 0) {
          tbody.innerHTML = data.logs.map(log => `
            <tr class="hover:bg-gray-800/30 transition">
              <td class="p-3 whitespace-nowrap text-gray-400 font-sans">${log.iso_time || 'N/A'}</td>
              <td class="p-3 text-indigo-300 font-sans">${log.chat_id}</td>
              <td class="p-3 max-w-xs truncate font-sans text-gray-200" title="${escapeHtml(log.user_message)}">${escapeHtml(log.user_message)}</td>
              <td class="p-3 max-w-xs truncate text-amber-300/80" title="${escapeHtml(log.code_executed || 'None')}">${log.code_executed ? '<code>' + escapeHtml(log.code_executed.substring(0, 35)) + '...</code>' : '<span class="text-gray-600">None</span>'}</td>
              <td class="p-3 max-w-xs truncate text-gray-300" title="${escapeHtml(String(log.answer))}">${escapeHtml(String(log.answer).substring(0, 50))}</td>
              <td class="p-3 whitespace-nowrap text-gray-400 font-sans">${log.duration_ms ? log.duration_ms + ' ms' : '--'}</td>
              <td class="p-3 whitespace-nowrap">
                ${log.error 
                  ? '<span class="px-2 py-0.5 rounded text-[10px] font-sans font-semibold bg-red-500/10 text-red-400 border border-red-500/20">Error</span>' 
                  : '<span class="px-2 py-0.5 rounded text-[10px] font-sans font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Success</span>'}
              </td>
            </tr>
          `).join('');
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    updateTelemetry();
    setInterval(updateTelemetry, 5000);
  </script>
</body>
</html>
"""
