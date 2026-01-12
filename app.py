from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory database
# Keyed by ID as strings to match frontend expectation
cards_data = {
    "1": {"id": 1, "status": "empty", "vehicle": "None", "entryTime": None},
    "2": {"id": 2, "status": "occupied", "vehicle": "KA-53-Z-9021", "entryTime": datetime.now().isoformat()},
    "3": {"id": 3, "status": "empty", "vehicle": "None", "entryTime": None}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartPark | Enterprise Parking</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts: Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Phosphor Icons -->
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                    },
                    colors: {
                        slate: {
                            850: '#1e293b', // Custom dark shade
                        }
                    }
                }
            }
        }
    </script>
    
    <style>
        body {
            background-color: #f8fafc; /* Slate-50 */
            background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
            background-size: 24px 24px;
            color: #0f172a; /* Slate-900 */
        }
        .glass-header {
            background: #0f172a; /* Slate-900 */
            backdrop-filter: blur(12px);
        }
        .card-tech {
            background: white;
            border: 1px solid #e2e8f0; /* Slate-200 */
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); /* shadow-sm */
            border-radius: 0.5rem; /* rounded-lg */
            transition: all 0.2s ease-in-out;
        }
        .card-tech:hover {
            border-color: #cbd5e1; /* Slate-300 */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-md */
        }
        .fade-in {
            animation: fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

    <!-- Solid Dark Header -->
    <nav class="sticky top-0 z-50 glass-header border-b border-slate-700">
        <div class="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3 cursor-pointer group" onclick="navigateHome()">
                <!-- Simple Monogram Logo -->
                <div class="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center border border-slate-700 shadow-sm group-hover:bg-slate-700 transition-colors">
                    <span class="text-white font-bold text-lg tracking-tight">SP</span>
                </div>
                <span class="font-bold text-xl tracking-tight text-white">SmartPark</span>
            </div>
            <div class="flex items-center gap-4">
                 <div id="connectionStatus" class="w-2 h-2 rounded-full bg-red-500 animate-pulse" title="System Status"></div>
                 <button id="logoutBtn" class="hidden text-xs font-bold bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-lg border border-slate-700 transition-colors text-white uppercase tracking-wider">Log Out</button>
            </div>
        </div>
    </nav>

    <!-- Main Container -->
    <main class="flex-grow w-full max-w-5xl mx-auto p-6 md:p-12 relative">
        <div id="app" class="w-full"></div>
    </main>
    
    <!-- Footer -->
    <footer class="py-10 border-t border-slate-200 mt-auto bg-white/50 backdrop-blur-sm">
         <div class="max-w-5xl mx-auto px-6 flex justify-between items-center text-sm text-slate-500">
            <p>&copy; SmartPark Systems</p>
            <div class="flex gap-4">
                <a href="#" class="hover:text-slate-800">Privacy</a>
                <a href="#" class="hover:text-slate-800">Status</a>
                <a href="#" class="hover:text-slate-800">API</a>
            </div>
         </div>
    </footer>

    <!-- JavaScript Strategy -->
    <script>
        // --- State ---
        let cardsData = {};
        const AUTH_KEY = 'smartpark_pro_auth';
        let isPolling = false;

        // --- Core Logic ---
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                if (!res.ok) throw new Error('Network err');
                const newCardsData = await res.json();

                const statusEl = document.getElementById('connectionStatus');
                statusEl.className = "w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-colors duration-300";
                
                // Deep compare to prevent stutter
                if (JSON.stringify(cardsData) !== JSON.stringify(newCardsData)) {
                    cardsData = newCardsData;
                    render();
                }

            } catch (e) {
                console.error("Sync Error", e);
                const statusEl = document.getElementById('connectionStatus');
                statusEl.className = "w-2 h-2 rounded-full bg-red-500 animate-pulse";
            }
        }

        async function updateCard(cardId, action, payload = {}) {
            try {
                const res = await fetch('/api/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cardId, action, ...payload })
                });
                const data = await res.json();
                if (data.error) alert(data.error);
                else {
                    await fetchStatus();
                    navigateHome();
                }
            } catch (e) {
                alert("Operation failed.");
            }
        }

        function init() {
            fetchStatus();
            setInterval(fetchStatus, 2000); 
            window.addEventListener('popstate', render);
            render();
            checkAuth();
        }

        function isLoggedIn() { return sessionStorage.getItem(AUTH_KEY) === 'true'; }

        function checkAuth() {
            const btn = document.getElementById('logoutBtn');
            if (isLoggedIn()) {
                btn.classList.remove('hidden');
                btn.onclick = () => { sessionStorage.removeItem(AUTH_KEY); window.location.reload(); };
            } else {
                btn.classList.add('hidden');
            }
        }

        function navigateHome() {
            history.pushState(null, '', '/');
            render();
        }
        
        function navigateToLogin() {
            history.pushState(null, '', '?view=login');
            render();
        }

        function navigateToCard(id) {
            history.pushState(null, '', `?card=${id}`);
            render();
        }

        function render() {
            const urlParams = new URLSearchParams(window.location.search);
            const cardId = urlParams.get('card');
            const view = urlParams.get('view');
            const app = document.getElementById('app');

            if (document.activeElement && document.activeElement.tagName === 'INPUT') return;

            if (cardId) {
                if (isLoggedIn()) renderManagerScan(app, cardId);
                else renderPublicScan(app, cardId);
            } else {
                if (isLoggedIn()) renderManagerDashboard(app);
                else if (view === 'login') renderLogin(app);
                else renderLanding(app);
            }
        }

        // --- Views ---

        function renderLanding(container) {
            container.innerHTML = `
                <div class="fade-in max-w-4xl mx-auto py-10">
                    <div class="text-center mb-16">
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold uppercase tracking-wide mb-6">
                            <span class="w-1.5 h-1.5 rounded-full bg-indigo-600"></span> Beta 2.0
                        </div>
                        <h1 class="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight mb-6">
                            Parking Intelligence <br>
                            <span class="text-slate-400">for Modern Cities.</span>
                        </h1>
                        <p class="text-lg text-slate-500 max-w-lg mx-auto leading-relaxed mb-10">
                            The enterprise-grade solution for vehicle management. Secure, fast, and built for scale.
                        </p>
                        
                        <div class="flex flex-col items-center gap-6">
                            <button onclick="navigateToLogin()" class="w-full max-w-xs bg-slate-900 hover:bg-black text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-slate-900/10 transition-all text-sm flex items-center justify-center gap-2 transform hover:-translate-y-1">
                                Access Console <i class="ph-bold ph-arrow-right"></i>
                            </button>
                            
                            <div class="flex items-center gap-0 divide-x divide-slate-100 bg-white p-1.5 rounded-xl border border-slate-200 shadow-sm">
                                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-3">Public Sim</span>
                                <div class="flex items-center px-1">
                                    ${[1, 2, 3].map(id => `
                                        <button onclick="navigateToCard(${id})" class="text-slate-500 hover:text-indigo-600 hover:bg-slate-50 font-bold text-sm w-8 h-8 rounded-lg transition-colors flex items-center justify-center">${id}</button>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Feature Grid -->
                    <div class="grid md:grid-cols-3 gap-6">
                        <div class="card-tech p-6">
                            <div class="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center text-indigo-600 mb-4 border border-indigo-100">
                                <i class="ph-bold ph-shield-check text-xl"></i>
                            </div>
                            <h3 class="font-bold text-slate-900 mb-2">Enterprise Security</h3>
                            <p class="text-sm text-slate-500 leading-relaxed">
                                Bank-grade encryption for all vehicle data and transaction logs.
                            </p>
                        </div>
                        <div class="card-tech p-6">
                            <div class="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center text-emerald-600 mb-4 border border-emerald-100">
                                <i class="ph-bold ph-lightning text-xl"></i>
                            </div>
                            <h3 class="font-bold text-slate-900 mb-2">Lightning Fast</h3>
                            <p class="text-sm text-slate-500 leading-relaxed">
                                Sub-millisecond response times for check-ins and check-outs.
                            </p>
                        </div>
                        <div class="card-tech p-6">
                            <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 mb-4 border border-blue-100">
                                <i class="ph-bold ph-chart-line-up text-xl"></i>
                            </div>
                            <h3 class="font-bold text-slate-900 mb-2">Real-time Analytics</h3>
                            <p class="text-sm text-slate-500 leading-relaxed">
                                Live dashboard updates with zero latency and high precision.
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderLogin(container) {
            container.innerHTML = `
                <div class="fade-in max-w-sm mx-auto mt-10">
                    <div class="card-tech border-t-4 border-t-indigo-500 p-8 shadow-lg">
                        <h2 class="text-xl font-bold text-slate-900 mb-1">Authenticated Access</h2>
                        <p class="text-sm text-slate-500 mb-6">Restricted to authorized personnel only.</p>

                        <form onsubmit="handleLogin(event)" class="space-y-4">
                            <div>
                                <label class="text-xs font-bold text-slate-700 uppercase tracking-wide block mb-1.5">Identity</label>
                                <input type="text" id="username" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2.5 text-slate-900 focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all text-sm font-medium" placeholder="admin">
                            </div>
                            <div>
                                <label class="text-xs font-bold text-slate-700 uppercase tracking-wide block mb-1.5">Key</label>
                                <input type="password" id="password" class="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2.5 text-slate-900 focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all text-sm font-medium" placeholder="••••">
                            </div>
                            <button type="submit" class="w-full bg-slate-900 hover:bg-black text-white font-bold py-2.5 rounded-lg text-sm transition-colors shadow-sm">
                                Authenticate
                            </button>
                        </form>
                    </div>
                     <button onclick="navigateHome()" class="w-full mt-6 text-xs font-bold text-slate-400 hover:text-slate-600 uppercase tracking-wider">Cancel Navigation</button>
                </div>
            `;
        }

        function handleLogin(e) {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            if (u === 'admin' && p === '123') {
                sessionStorage.setItem(AUTH_KEY, 'true');
                checkAuth();
                render();
            } else {
                alert('Access Denied.');
            }
        }

        function renderManagerDashboard(container) {
            let html = `
                <div class="fade-in">
                    <div class="flex items-end justify-between mb-6">
                        <div>
                            <h2 class="text-2xl font-bold text-slate-900 tracking-tight">Overview</h2>
                            <p class="text-sm text-slate-500 font-medium">Facility status and controls</p>
                        </div>
                        <div class="flex gap-2">
                             <span class="px-3 py-1 bg-white border border-slate-200 rounded-md text-xs font-bold text-slate-600 shadow-sm">
                                Total Spots: 3
                             </span>
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-4 gap-6">
                        <!-- Sidebar / Stats -->
                        <div class="hidden md:block space-y-4">
                            <div class="card-tech p-4">
                                <p class="text-xs font-bold text-slate-400 uppercase mb-1">Occupancy</p>
                                <div class="text-3xl font-bold text-slate-900">${Object.values(cardsData).filter(c => c.status === 'occupied').length} <span class="text-slate-300 text-lg">/ 3</span></div>
                            </div>
                             <div class="card-tech p-4 bg-slate-50 border-slate-200/50">
                                <p class="text-xs font-bold text-slate-400 uppercase mb-2">Recent Activity</p>
                                <div class="space-y-3">
                                    <div class="flex items-center gap-2 text-xs text-slate-500">
                                        <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div> System Online
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Main Grid -->
                        <div class="md:col-span-3 grid sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            `;

            const ids = [1, 2, 3];
            ids.forEach(id => {
                const card = cardsData[id.toString()] || { id: id, status: 'unknown' };
                const isOcc = card.status === 'occupied';
                
                html += `
                    <div class="card-tech p-5 flex flex-col justify-between h-48 relative overflow-hidden group ${isOcc ? 'border-l-4 border-l-emerald-500' : 'border-l-4 border-l-slate-200'}">
                        <div>
                            <div class="flex justify-between items-start mb-3">
                                <span class="font-mono text-xs font-bold text-slate-400">#00${id}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                                    isOcc 
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                    : 'bg-slate-50 text-slate-500 border-slate-100'
                                }">
                                    ${card.status === 'unknown' ? 'SYNC' : (isOcc ? 'Active' : 'Idle')}
                                </span>
                            </div>
                            <h3 class="text-lg font-bold text-slate-800 mb-1">
                                ${isOcc ? card.vehicle : 'Available'}
                            </h3>
                            ${isOcc ? `
                                <p class="text-xs text-slate-500 font-mono">
                                    ${new Date(card.entryTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                            ` : ''}
                        </div>

                        <button onclick="navigateToCard(${id})" class="mt-4 w-full py-2 rounded border border-slate-200 bg-white text-slate-600 text-xs font-bold uppercase hover:bg-slate-50 hover:border-slate-300 transition-all flex items-center justify-center gap-2">
                            ${isOcc ? 'View Details' : 'Initiate Entry'}
                        </button>
                    </div>
                `;
            });
            html += `</div></div></div>`;
            container.innerHTML = html;
        }

        function renderManagerScan(container, cardId) {
            const card = cardsData[cardId];
            if (!card) return container.innerHTML = renderLoader();

            // Check In
            if (card.status === 'empty') {
                container.innerHTML = `
                    <div class="fade-in max-w-lg mx-auto mt-8">
                         <div class="flex items-center gap-4 mb-6">
                            <button onclick="navigateHome()" class="w-8 h-8 flex items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-white transition-colors">
                                <i class="ph-bold ph-arrow-left"></i>
                            </button>
                            <h2 class="text-xl font-bold text-slate-900">Entry Protocol <span class="text-slate-400">#${cardId}</span></h2>
                         </div>

                        <div class="card-tech p-8 border-t-4 border-t-indigo-500 shadow-md bg-white">
                             <div class="space-y-6">
                                 <div>
                                    <label class="block text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Vehicle Registration</label>
                                    <input id="vIn" type="text" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-lg font-mono uppercase text-slate-900 placeholder-slate-400 focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="KA-05-XY-1234">
                                 </div>
                                 
                                 <div>
                                    <label class="block text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Contact (Optional)</label>
                                    <input id="pIn" type="tel" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-3 text-slate-900 placeholder-slate-400 focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all" placeholder="98765...">
                                 </div>

                                 <button onclick="handleCheckIn(${cardId})" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-lg shadow-sm transition-all flex items-center justify-center gap-2 mt-2">
                                    <i class="ph-bold ph-check"></i>
                                    Authorize Entry
                                 </button>
                             </div>
                        </div>
                    </div>
                `;
            } 
            // Check Out
            else {
                const diff = card.entryTime ? Math.round((new Date() - new Date(card.entryTime)) / 60000) : 0;
                const cost = Math.max(50, diff * 1);

                container.innerHTML = `
                    <div class="fade-in max-w-lg mx-auto mt-8">
                         <div class="flex items-center gap-4 mb-6">
                            <button onclick="navigateHome()" class="w-8 h-8 flex items-center justify-center rounded-full border border-slate-200 text-slate-500 hover:bg-white transition-colors">
                                <i class="ph-bold ph-arrow-left"></i>
                            </button>
                            <h2 class="text-xl font-bold text-slate-900">Exit Protocol <span class="text-slate-400">#${cardId}</span></h2>
                         </div>

                        <div class="card-tech p-0 border-t-4 border-t-emerald-500 shadow-md bg-white overflow-hidden">
                             <div class="p-6 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                                <div>
                                    <p class="text-xs font-bold text-slate-500 uppercase mb-1">Vehicle</p>
                                    <h3 class="text-2xl font-mono font-bold text-slate-900">${card.vehicle}</h3>
                                </div>
                                <div class="text-right">
                                    <p class="text-xs font-bold text-slate-500 uppercase mb-1">Duration</p>
                                    <p class="text-lg font-bold text-indigo-600">${diff}m</p>
                                </div>
                             </div>
                             
                             <div class="p-8">
                                <div class="flex justify-between items-end mb-8">
                                    <span class="text-sm font-bold text-slate-500">Total Due</span>
                                    <span class="text-4xl font-bold text-slate-900 tracking-tight">₹${cost}</span>
                                </div>

                                <button onclick="handleCheckOut(${cardId})" class="w-full bg-slate-900 hover:bg-black text-white font-bold py-3 rounded-lg shadow-sm transition-all flex items-center justify-center gap-2">
                                    <i class="ph-bold ph-receipt"></i>
                                    Process Payment & Release
                                </button>
                             </div>
                        </div>
                    </div>
                `;
            }
        }

        function handleCheckIn(id) {
            const v = document.getElementById('vIn').value;
            const p = document.getElementById('pIn').value;
            if (!v) return alert("Registration Required");
            updateCard(id, 'checkin', { vehicle: v, phone: p });
        }

        function handleCheckOut(id) {
            if (confirm("Confirm Payment & Exit?")) {
                updateCard(id, 'checkout');
            }
        }

        function renderPublicScan(container, cardId) {
            const card = cardsData[cardId];
            if (!card) return container.innerHTML = renderLoader();

            if (card.status === 'empty') {
                container.innerHTML = `
                    <div class="fade-in text-center mt-20 px-6 max-w-md mx-auto">
                        <div class="w-16 h-16 bg-white border border-slate-200 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-sm">
                             <i class="ph-duotone ph-check-circle text-4xl text-emerald-500"></i>
                        </div>
                        <h2 class="text-xl font-bold text-slate-900 mb-2">Spot #00${cardId} Available</h2>
                        <p class="text-slate-500 text-sm mb-8 leading-relaxed">This unit is currently unoccupied and ready for assignment.</p>
                        
                        <a href="/" class="text-indigo-600 font-bold hover:text-indigo-800 transition-colors text-xs uppercase tracking-wide">Staff Access</a>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="fade-in max-w-md mx-auto mt-6 px-4">
                        <div class="card-tech p-8 border-t-4 border-t-slate-900 text-center">
                            <div class="inline-flex items-center gap-2 px-3 py-1 bg-red-50 border border-red-100 rounded-full text-red-700 text-xs font-bold uppercase tracking-wide mb-8">
                                <span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span> Occupied
                            </div>

                            <div class="mb-8">
                                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Registered Vehicle</p>
                                <h1 class="text-3xl font-mono font-bold text-slate-900 tracking-tight">${card.vehicle}</h1>
                            </div>

                            <a href="tel:${card.phone}" class="w-full bg-slate-900 hover:bg-black text-white font-bold py-3.5 rounded-lg shadow-sm transition-all flex items-center justify-center gap-2">
                                 <i class="ph-bold ph-phone"></i>
                                 Contact Owner
                            </a>
                        </div>
                        
                        <button onclick="navigateHome()" class="mt-8 text-slate-400 text-xs font-bold hover:text-slate-600 uppercase tracking-wider">Return to Console</button>
                    </div>
                `;
            }
        }

        function renderLoader() {
            return `
                <div class="flex flex-col items-center justify-center mt-32 text-slate-400 space-y-4">
                    <i class="ph-bold ph-spinner animate-spin text-2xl text-indigo-600"></i>
                    <p class="text-xs font-bold tracking-widest uppercase">Connecting...</p>
                </div>
            `;
        }

        window.onload = init;
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(cards_data)

@app.route('/api/update', methods=['POST'])
def update_status():
    data = request.json
    card_id = str(data.get('cardId'))
    action = data.get('action')
    
    if card_id in cards_data:
        if action == 'checkin':
            cards_data[card_id]['status'] = 'occupied'
            cards_data[card_id]['vehicle'] = data.get('vehicle', 'Unknown')
            cards_data[card_id]['phone'] = data.get('phone', '')
            cards_data[card_id]['entryTime'] = datetime.now().isoformat()
        
        elif action == 'checkout':
            cards_data[card_id]['status'] = 'empty'
            cards_data[card_id]['vehicle'] = 'None'
            cards_data[card_id]['entryTime'] = None
            
    return jsonify({"message": "Success", "data": cards_data[card_id]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
