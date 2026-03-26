/**
 * EcoPower Web Edition - Game Logic Engine
 * 
 * This file is a pixel-perfect logic port of the Python version.
 * It handles the 25-level progression, sustainability mechanics,
 * and the BFS-based power distribution algorithm.
 */

const COLORS = {
    bg: "#2E3440",
    bgDarker: "#242933",
    fg: "#ECEFF4",
    green: "#A3BE8C",
    red: "#BF616A",
    yellow: "#EBCB8B",
    blue: "#88C0D0",
    orange: "#D08770",
    nord4: "#D8DEE9",
    nord10: "#5E81AC"
};

class WorldState {
    constructor() {
        this.time = 0.35; // 0.0 to 1.0 (midday at 0.5)
        this.wind = 0.5;
        this.water = 0.8;
        this.lastUpdate = Date.now();
    }

    update() {
        const now = Date.now();
        const dt = (now - this.lastUpdate) / 1000;
        this.lastUpdate = now;

        // Cycle time: 1 minute per day
        this.time = (this.time + dt / 60) % 1.0;
        
        // Random wind fluctuation
        this.wind = Math.max(0.1, Math.min(1.0, this.wind + (Math.random() * 0.1 - 0.05)));
    }
}

class Node {
    constructor(id, type, x, y, name) {
        this.id = id;
        this.type = type;
        this.x = x;
        this.y = y;
        this.name = name;
        this.energy_atual = 0;
        this.capacidade_maxima = 0;
        this.capacidade_atual = 0;
        this.demanda = 0;
        this.radius = 35;
        this.color = COLORS.nord4;
    }
}

class Generator extends Node {
    constructor(id, x, y, name, capacity, genType = "PADRAO") {
        super(id, "gerador", x, y, name);
        this.capacidade_maxima = capacity;
        this.capacidade_atual = capacity;
        this.gen_type = genType;
        this.updateStats();
    }

    updateStats() {
        if (this.gen_type === "SOLAR") this.color = COLORS.yellow;
        else if (this.gen_type === "EOLICA") this.color = COLORS.blue;
        else if (this.gen_type === "HIDRELETRICA") this.color = COLORS.nord10;
        else if (this.gen_type === "TERMELETRICA") this.color = "#4C566A";
        else if (this.gen_type === "NUCLEAR") this.color = COLORS.red;
        else this.color = COLORS.orange;
    }
}

class Battery extends Node {
    constructor(id, x, y, name, maxStorage = 100) {
        super(id, "bateria", x, y, name);
        this.capacidade_maxima = 20; // Max discharge rate
        this.capacidade_atual = 20;
        this.max_storage = maxStorage;
        this.stored_energy = 0;
        this.color = COLORS.green;
        this.radius = 35;
    }
}

class City extends Node {
    constructor(id, x, y, name, demand) {
        super(id, "cidade", x, y, name);
        this.demanda = demand;
        this.radius = 45;
        this.color = "#81A1C1";
    }
}

class Substation extends Node {
    constructor(id, x, y, name) {
        super(id, "subestacao", x, y, name);
        this.radius = 30;
        this.color = COLORS.blue;
    }
}

class Edge {
    constructor(n1, n2, capacity = 8, type = "ALUMINIO") {
        this.n1 = n1;
        this.n2 = n2;
        this.capacidade_maxima = capacity;
        this.carga_atual = 0;
        this.type = type;
        this.failed = false;
    }

    getOther(node) {
        return node === this.n1 ? this.n2 : this.n1;
    }
}

class Game {
    constructor() {
        this.nodes = [];
        this.edges = [];
        this.world = new WorldState();
        this.difficulty = "Normal";
        this.mode = "EDUCACIONAL";
        this.currentLevel = 1;
        this.powerOn = false;
        this.state = "RUNNING";
        this.selectedNode = null;
        this.creativeItem = "Subestação";
        this.currentCategory = "⚡ GERAÇÃO";
        
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.init();
    }

    init() {
        window.addEventListener('resize', () => this.resize());
        this.resize();
        
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('contextmenu', (e) => { e.preventDefault(); this.handleRightClick(e); });
        
        document.getElementById('btn-power').onclick = () => this.togglePower();
        document.getElementById('btn-reset').onclick = () => this.resetLevel();
        document.getElementById('btn-menu').onclick = () => location.reload();
        document.getElementById('btn-help').onclick = () => this.showHelp();
        document.getElementById('btn-next').onclick = () => this.nextLevel();
        
        this.setupCreativeUI();
        
        // Game Loop
        setInterval(() => this.update(), 100);
    }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.render();
    }

    update() {
        if (this.mode !== "EDUCACIONAL" && this.powerOn) {
            this.world.update();
            this.updateFlow();
            this.updateHUD();
        }
        this.render();
    }

    updateHUD() {
        if (this.mode !== "EDUCACIONAL") {
            document.getElementById('world-hud').classList.remove('hidden');
            const h = Math.floor(this.world.time * 24);
            const m = Math.floor((this.world.time * 24 % 1) * 60);
            document.getElementById('lbl-time').innerText = `🕒 ${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
            
            const sun = this.world.time >= 0.25 && this.world.time <= 0.75 ? 100 : 0;
            const wind = Math.floor(this.world.wind * 100);
            document.getElementById('lbl-env').innerText = `☀️ ${sun}% | 🌬️ ${wind}%`;
        } else {
            document.getElementById('world-hud').classList.add('hidden');
        }

        if (this.mode === "SUSTENTAVEL") {
            document.getElementById('sustainability-container').classList.remove('hidden');
            const idx = this.getSustainabilityIndex();
            document.getElementById('sus-progress').style.width = `${idx}%`;
            document.getElementById('sus-progress').style.background = idx > 70 ? COLORS.green : COLORS.red;
            document.getElementById('lbl-sus').innerText = `Sustentabilidade: ${idx}%`;
        } else {
            document.getElementById('sustainability-container').classList.add('hidden');
        }
        
        document.getElementById('lbl-fase').innerText = `FASE ${this.currentLevel}/25`;
    }

    startGame(mode) {
        this.mode = mode;
        this.currentLevel = 1;
        document.getElementById('menu-overlay').classList.add('hidden');
        
        if (mode === "CRIATIVO") {
            document.getElementById('sidebar').classList.remove('hidden');
            this.nodes = [];
            this.edges = [];
        } else {
            document.getElementById('sidebar').classList.add('hidden');
            this.buildLevel();
        }
        this.updateHUD();
    }

    buildLevel() {
        this.nodes = [];
        this.edges = [];
        this.powerOn = false;
        this.state = "RUNNING";
        
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        let numG = 1 + Math.floor(this.currentLevel / 6);
        let numS = 2 + Math.floor(this.currentLevel / 4);
        let numC = 1 + Math.floor(this.currentLevel / 5);
        
        if (this.difficulty === "Normal") {
            numG = 2 + Math.floor(this.currentLevel / 6);
            numS = 2 + Math.floor(this.currentLevel / 3);
            numC = 2 + Math.floor(this.currentLevel / 4);
        }

        const genTypes = [];
        for (let i = 0; i < numG; i++) {
            if (this.mode === "SUSTENTAVEL") {
                const pool = ["SOLAR", "EOLICA", "HIDRELETRICA", "TERMELETRICA"];
                genTypes.push(pool[Math.floor(Math.random() * pool.length)]);
            } else {
                genTypes.push("PADRAO");
            }
        }

        for (let i = 0; i < numG; i++) {
            const x = 100 + Math.random() * 100;
            const y = 100 + (h - 200) / numG * i;
            this.nodes.push(new Generator(i, x, y, `G${i+1}`, 15 + Math.floor(Math.random() * 10), genTypes[i]));
        }

        for (let i = 0; i < numS; i++) {
            const x = w/2 + (Math.random() * 200 - 100);
            const y = 100 + (h - 200) / numS * i;
            this.nodes.push(new Substation(numG + i, x, y, `Sub ${String.fromCharCode(65+i)}`));
        }

        for (let i = 0; i < numC; i++) {
            const x = w - 150 - Math.random() * 100;
            const y = 100 + (h - 200) / numC * i;
            this.nodes.push(new City(numG + numS + i, x, y, `Cidade ${i+1}`, 10 + Math.floor(Math.random() * 15)));
        }
        
        this.render();
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const clickedNode = this.nodes.find(n => Math.hypot(n.x - x, n.y - y) < n.radius + 5);
        
        if (this.mode === "CRIATIVO" && !clickedNode) {
            this.placeItem(x, y);
            return;
        }

        if (clickedNode) {
            if (this.selectedNode) {
                if (this.selectedNode !== clickedNode) {
                    this.createEdge(this.selectedNode, clickedNode);
                }
                this.selectedNode = null;
            } else {
                this.selectedNode = clickedNode;
            }
        }
        this.render();
    }

    handleRightClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Try to remove edge first
        const edgeIdx = this.edges.findIndex(edge => {
            const dx = edge.n2.x - edge.n1.x;
            const dy = edge.n2.y - edge.n1.y;
            const len = Math.hypot(dx, dy);
            const dist = Math.abs(dy * x - dx * y + edge.n2.x * edge.n1.y - edge.n2.y * edge.n1.x) / len;
            return dist < 10;
        });

        if (edgeIdx !== -1) {
            this.edges.splice(edgeIdx, 1);
            this.updateFlow();
            return;
        }

        // Try to remove node
        const nodeIdx = this.nodes.findIndex(n => Math.hypot(n.x - x, n.y - y) < n.radius + 5);
        if (nodeIdx !== -1) {
            const node = this.nodes[nodeIdx];
            this.nodes.splice(nodeIdx, 1);
            this.edges = this.edges.filter(e => e.n1 !== node && e.n2 !== node);
            this.updateFlow();
        }
    }

    createEdge(n1, n2) {
        const exists = this.edges.some(e => (e.n1 === n1 && e.n2 === n2) || (e.n1 === n2 && e.n2 === n1));
        if (!exists) {
            const cap = this.difficulty === "Fácil" ? 8 : 5;
            this.edges.push(new Edge(n1, n2, cap));
            this.updateFlow();
        }
    }

    placeItem(x, y) {
        const id = Date.now();
        switch(this.creativeItem) {
            case "Solar": this.nodes.push(new Generator(id, x, y, "Solar", 10, "SOLAR")); break;
            case "Eólico": this.nodes.push(new Generator(id, x, y, "Eólico", 12, "EOLICA")); break;
            case "Hidro": this.nodes.push(new Generator(id, x, y, "Hidro", 25, "HIDRELETRICA")); break;
            case "Nuclear": this.nodes.push(new Generator(id, x, y, "Nuclear", 100, "NUCLEAR")); break;
            case "Cid. Pequena": this.nodes.push(new City(id, x, y, "Cid Pequena", 10)); break;
            case "Cid. Grande": this.nodes.push(new City(id, x, y, "Cid Grande", 40)); break;
            case "Subestação": this.nodes.push(new Substation(id, x, y, "Sub")); break;
            case "Bateria": this.nodes.push(new Battery(id, x, y, "Bateria")); break;
        }
    }

    togglePower() {
        this.powerOn = !this.powerOn;
        const btn = document.getElementById('btn-power');
        btn.innerText = this.powerOn ? '■ DESLIGAR REDE' : '▶ LIGAR REDE';
        btn.className = this.powerOn ? 'btn-power-on' : 'btn-power-off';
        this.updateFlow();
    }

    updateFlow() {
        this.nodes.forEach(n => {
            n.energy_atual = 0;
            if (n instanceof Generator) {
                n.capacidade_atual = n.capacidade_maxima;
                if (this.mode !== "EDUCACIONAL") {
                    if (n.gen_type === "SOLAR") {
                        const sun = (this.world.time >= 0.25 && this.world.time <= 0.75) ? 1.0 : 0.0;
                        n.capacidade_atual *= sun;
                    } else if (n.gen_type === "EOLICA") {
                        n.capacidade_atual *= this.world.wind;
                    }
                }
            }
        });
        this.edges.forEach(e => e.carga_atual = 0);
        
        if (!this.powerOn) return;

        const sources = this.nodes.filter(n => n.type === 'gerador' || (n instanceof Battery && n.stored_energy > 0));
        let powerMoved = true;
        while (powerMoved) {
            powerMoved = false;
            for (let source of sources) {
                const cap = source.type === 'gerador' ? source.capacidade_atual : Math.min(source.stored_energy, source.capacidade_maxima);
                if (source.energy_atual < cap) {
                    const path = this.findPathToCity(source);
                    if (path) {
                        source.energy_atual++;
                        path.forEach(edge => edge.carga_atual++);
                        powerMoved = true;
                    }
                }
            }
        }
        this.checkVictory();
    }

    findPathToCity(startNode) {
        const queue = [[startNode, []]];
        const visited = new Set([startNode]);
        
        while (queue.length > 0) {
            const [current, path] = queue.shift();
            
            if (current.type === 'cidade' && current.energy_atual < current.demanda) {
                current.energy_atual++; 
                return path;
            }
            
            const adjEdges = this.edges.filter(e => (e.n1 === current || e.n2 === current) && !e.failed);
            for (let edge of adjEdges) {
                if (edge.carga_atual < edge.capacidade_maxima) {
                    const next = edge.getOther(current);
                    if (!visited.has(next)) {
                        visited.add(next);
                        queue.push([next, [...path, edge]]);
                    }
                }
            }
        }
        return null;
    }

    getSustainabilityIndex() {
        const total = this.nodes.filter(n => n.type === 'gerador').reduce((acc, n) => acc + n.energy_atual, 0);
        if (total === 0) return 100;
        const dirty = this.nodes.filter(n => n.gen_type === "TERMELETRICA" || n.gen_type === "NUCLEAR").reduce((acc, n) => acc + n.energy_atual, 0);
        return Math.floor(((total - dirty) / total) * 100);
    }

    checkVictory() {
        if (this.mode === "CRIATIVO") return;
        const cities = this.nodes.filter(n => n.type === 'cidade');
        const allSatisfied = cities.every(c => c.energy_atual >= c.demanda);
        
        if (allSatisfied && this.powerOn && this.state !== "WIN") {
            this.state = "WIN";
            setTimeout(() => this.showVictoryModal(), 500);
        }
    }

    showVictoryModal() {
        document.getElementById('victory-modal').classList.remove('hidden');
        document.getElementById('vic-msg').innerText = this.getVictoryMessage();
    }

    nextLevel() {
        document.getElementById('victory-modal').classList.add('hidden');
        this.currentLevel++;
        if (this.currentLevel > 25) {
            alert("VOCÊ COMPLETOU O MODO EDUCATIVO! PARABÉNS!");
            location.reload();
        } else {
            this.buildLevel();
        }
    }

    getVictoryMessage() {
        const messages = [
            "Muito bem! Você conectou a fonte de energia à cidade. Entender como o fluxo viaja do gerador até a casa é o primeiro passo da engenharia elétrica.",
            "Excelente! Você usou subestações como intermediárias. Elas ajudam a organizar a rede e permitem que o sistema cresça de forma modular e segura.",
            "Ótimo! Você descobriu que geradores podem trabalhar juntos. Somar a geração em um 'Grid' é o que permite alimentar cidades inteiras com estabilidade.",
            "Incrível! Ao equilibrar as fontes, você evitou que um único gerador ficasse sobrecarregado. O balanceamento é a chave para uma rede duradoura.",
            "Parabéns! Você concluiu a etapa básica de transmissão simples. Agora as redes ficarão mais complexas e exigirão caminhos paralelos.",
            "Circuitos Paralelos: Ao notar que o cabo não aguentava toda a carga, você dividiu o fluxo. Isso reduz o aquecimento dos fios e aumenta a segurança térmica.",
            "Redundância: Criar caminhos alternativos garante que, se um cabo falhar, a cidade não pare. É o conceito de resiliência elétrica urbana.",
            "Estabilidade Térmica: Ao distribuir a carga, você evitou que os elétrons sobrecarregassem as subestações. Menos estresse significa menos blackouts.",
            "Margem de Segurança: Engenheiros nunca trabalham no limite. Deixar folga nos cabos permite que a cidade cresça sem precisar refazer toda a fiação.",
            "Controle de Fluxo: Agora você domina como a energia se divide. A eletricidade sempre busca o caminho de menor resistência, mas você a guiou com maestria.",
            "Gerenciamento de Pico: Você distribuiu o esforço de geradores potentes. Antecipar onde a carga será maior é vital para não saturar o centro da cidade.",
            "Arquitetura em Estrela: Usar uma subestação central facilita o monitoramento e permite isolar falhas sem derrubar o sistema inteiro.",
            "Eficiência Magnética: Você evitou gargalos. Quando muitos elétrons tentam passar por um cabo fino, a resistência gera calor e desperdício de energia.",
            "Setorização: Ao separar áreas industriais de residenciais, você garantiu que uma falha em uma fábrica não desligasse o hospital vizinho.",
            "Ponto de Entrega: Você atingiu a metade do caminho! O uso de estações intermediárias garante que a voltagem chegue estabilizada nas tomadas.",
            "Estabilidade do Sistema: Adicionar fontes em uma malha ativa exige cuidado. Você soube integrar a nova geração sem desequilibrar a carga existente.",
            "Manutenção Geográfica: Você levou energia para longe. Cabos longos perdem voltagem; suas estações de apoio reforçaram a qualidade da entrega.",
            "Infraestrutura Crítica: Você provou que entende os limites térmicos. Economizar em cabos gera um risco inaceitável de blackout econômico.",
            "Otimização de Fluxo: A energia elétrica não escolhe o caminho que você quer, mas o mais fácil. Você a domou através de rotas seguras.",
            "Resiliência sob Estresse: Mesmo com alta demanda, sua rede se manteve equilibrada. Um sistema estável opera de forma silenciosa e eficiente.",
            "Sistemas de Grande Porte: Você gerenciou múltiplas fontes e consumidores. A sincronia entre geração e demanda é o coração do sistema elétrico.",
            "Smart Grids: Antecipar gargalos e reforçar a malha antes de ligar os disjuntores é a base das redes inteligentes do futuro.",
            "Segurança N-1: O sistema deve operar mesmo se UMA conexão falhar. Sua rede sobreviveu a imprevistos técnicos e manteve a ordem.",
            "Engenharia de Proteção: Ver o grid como um todo, e não apenas fios isolados, permitiu que você resolvesse este layout espacial complexo.",
            "Mestre da Engenharia: Parabéns! Você domina a geração e distribuição. Está pronto para projetar grades elétricas seguras e eficientes!"
        ];
        return messages[this.currentLevel - 1] || "Parabéns por completar este desafio de engenharia!";
    }

    setupCreativeUI() {
        const cats = {
            "⚡ GERAÇÃO": ["Solar", "Eólico", "Hidro", "Nuclear", "Termelétrica"],
            "🔌 DISTRIB": ["Subestação", "Poste", "Bateria"],
            "🏘️ DEMANDA": ["Cid. Pequena", "Cid. Grande"]
        };
        const selector = document.getElementById('category-selector');
        Object.keys(cats).forEach(cat => {
            const btn = document.createElement('button');
            btn.className = "cat-btn";
            btn.innerText = cat;
            btn.onclick = () => this.showCategory(cat, cats);
            selector.appendChild(btn);
        });
        this.showCategory("⚡ GERAÇÃO", cats);
    }

    showCategory(cat, cats) {
        this.currentCategory = cat;
        const list = document.getElementById('item-list');
        list.innerHTML = "";
        cats[cat].forEach(item => {
            const btn = document.createElement('button');
            btn.className = "item-btn btn-secondary";
            btn.innerText = item;
            btn.onclick = () => {
                this.creativeItem = item;
                this.render();
            };
            list.appendChild(btn);
        });
    }

    render() {
        const { ctx, canvas } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.strokeStyle = "rgba(136, 192, 208, 0.05)";
        ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=40) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,canvas.height); ctx.stroke(); }
        for(let j=0; j<canvas.height; j+=40) { ctx.beginPath(); ctx.moveTo(0,j); ctx.lineTo(canvas.width,j); ctx.stroke(); }

        this.edges.forEach(e => {
            ctx.beginPath();
            ctx.moveTo(e.n1.x, e.n1.y);
            ctx.lineTo(e.n2.x, e.n2.y);
            let color = COLORS.green;
            if (e.carga_atual > e.capacidade_maxima) color = COLORS.red;
            else if (e.carga_atual > e.capacidade_maxima * 0.9) color = COLORS.yellow;
            ctx.strokeStyle = color;
            ctx.lineWidth = 4;
            ctx.stroke();
            if (this.powerOn && e.carga_atual > 0) {
                const mx = (e.n1.x + e.n2.x) / 2;
                const my = (e.n1.y + e.n2.y) / 2;
                ctx.fillStyle = "rgba(0,0,0,0.7)";
                ctx.fillRect(mx-20, my-10, 40, 20);
                ctx.fillStyle = "white";
                ctx.font = "bold 10px Arial";
                ctx.fillText(`${e.carga_atual}/${e.capacidade_maxima}`, mx, my + 4);
            }
        });

        this.nodes.forEach(n => {
            ctx.fillStyle = COLORS.bg;
            ctx.strokeStyle = n.color;
            ctx.lineWidth = 3;
            if (n.type === 'gerador') {
                ctx.strokeRect(n.x - 30, n.y - 30, 60, 60);
                ctx.fillStyle = "white";
                ctx.fillText(n.name, n.x, n.y - 5);
                ctx.fillText(`${n.energy_atual}/${n.capacidade_atual}`, n.x, n.y + 15);
            } else if (n.type === 'cidade') {
                ctx.beginPath(); ctx.moveTo(n.x, n.y - 35); ctx.lineTo(n.x + 35, n.y); ctx.lineTo(n.x + 25, n.y + 25); ctx.lineTo(n.x - 25, n.y + 25); ctx.lineTo(n.x - 35, n.y); ctx.closePath();
                ctx.stroke(); ctx.fillStyle = "white"; ctx.fillText(`${n.energy_atual}/${n.demanda}`, n.x, n.y + 12);
            } else {
                ctx.beginPath(); ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = "white"; ctx.fillText(n.name, n.x, n.y + 5);
            }
            if (this.selectedNode === n) {
                ctx.setLineDash([5, 5]); ctx.strokeStyle = "white"; ctx.strokeRect(n.x - 45, n.y - 45, 90, 90); ctx.setLineDash([]);
            }
        });
    }

    showHelp() {
        document.getElementById('help-modal').classList.remove('hidden');
        document.getElementById('help-text').innerText = this.mode === "EDUCACIONAL" ? 
            "Ligue o gerador à subestação e à cidade. Use fios paralelos se notar sobrecarga (cabo vermelho)." :
            "Mantenha o índice de sustentabilidade alto usando fontes renováveis. Baterias ajudam a estocar energia solar.";
    }
}

let game = new Game();
function startGame(mode) { game.startGame(mode); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
window.onload = () => { game.render(); };
