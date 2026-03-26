const COLORS = {
    bg: "#2E3440",
    bgDarker: "#242933",
    fg: "#ECEFF4",
    green: "#A3BE8C",
    red: "#BF616A",
    yellow: "#EBCB8B",
    blue: "#88C0D0",
    orange: "#D08770",
    nord4: "#D8DEE9"
};

class Node {
    constructor(id, type, x, y, name, capacity = 0, demand = 0) {
        this.id = id;
        this.type = type;
        this.x = x;
        this.y = y;
        this.name = name;
        this.capacidade_maxima = capacity;
        this.capacidade_atual = capacity;
        this.energy_atual = 0;
        this.demanda = demand;
        this.gen_type = "PADRAO";
        this.color = type === "gerador" ? COLORS.orange : (type === "cidade" ? COLORS.blue : COLORS.nord4);
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
        this.mode = 'EDUCACIONAL';
        this.difficulty = 'Fácil';
        this.currentLevel = 1;
        this.powerOn = false;
        this.selectedNode = null;
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.init();
    }

    init() {
        window.addEventListener('resize', () => this.resize());
        this.resize();
        
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        
        document.getElementById('btn-power').onclick = () => this.togglePower();
        document.getElementById('btn-reset').onclick = () => this.resetLevel();
        document.getElementById('btn-help').onclick = () => this.showHelp();
    }

    resize() {
        this.canvas.width = this.canvas.clientWidth;
        this.canvas.height = this.canvas.clientHeight;
        this.render();
    }

    startGame(mode) {
        this.mode = mode;
        this.currentLevel = 1;
        document.getElementById('menu-overlay').classList.add('hidden');
        if (mode === 'CRIATIVO') {
            document.getElementById('sidebar').classList.remove('hidden');
        } else {
            document.getElementById('sidebar').classList.add('hidden');
            this.buildLevel();
        }
    }

    buildLevel() {
        this.nodes = [];
        this.edges = [];
        this.powerOn = false;
        
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        // Simple logic for Level 1 demo - will expand for full procedural
        this.nodes.push(new Node(0, "gerador", 100, h/2, "Gerador 1", 20));
        this.nodes.push(new Node(1, "subestacao", w/2, h/2, "Sub A"));
        this.nodes.push(new Node(2, "subestacao", w/2, h/2 + 100, "Sub B"));
        this.nodes.push(new Node(3, "cidade", w - 150, h/2, "Cidade 1", 0, 15));
        
        this.render();
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const clickedNode = this.nodes.find(n => Math.hypot(n.x - x, n.y - y) < 40);
        
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

    createEdge(n1, n2) {
        const exists = this.edges.some(e => (e.n1 === n1 && e.n2 === n2) || (e.n1 === n2 && e.n2 === n1));
        if (!exists) {
            this.edges.push(new Edge(n1, n2));
            this.updateFlow();
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
        // Core BFS Logic (Simplified version for initial web port)
        this.nodes.forEach(n => n.energy_atual = 0);
        this.edges.forEach(e => e.carga_atual = 0);
        
        if (!this.powerOn) {
            this.render();
            return;
        }

        const generators = this.nodes.filter(n => n.type === 'gerador');
        const cities = this.nodes.filter(n => n.type === 'cidade');
        
        // Distribute energy MW by MW (Step-wise to allow balancing as in Python version)
        let powerMoved = true;
        while (powerMoved) {
            powerMoved = false;
            for (let gen of generators) {
                if (gen.energy_atual < gen.capacidade_atual) {
                    const path = this.findPathToCity(gen);
                    if (path) {
                        gen.energy_atual++;
                        path.forEach(edge => edge.carga_atual++);
                        powerMoved = true;
                    }
                }
            }
        }
        this.render();
    }

    findPathToCity(startNode) {
        // BFS for the shortest clean path
        const queue = [[startNode, []]];
        const visited = new Set([startNode]);
        
        while (queue.length > 0) {
            const [current, path] = queue.shift();
            
            if (current.type === 'cidade' && current.energy_atual < current.demanda) {
                current.energy_atual++; // Internal tracker for pathfinding
                return path;
            }
            
            const adjEdges = this.edges.filter(e => (e.n1 === current || e.n2 === current) && !e.failed);
            for (let edge of adjEdges) {
                // Prefira caminhos não sobrecarregados
                if (edge.carga_atual < edge.capacidade_maxima) {
                    const next = edge.getOther(current);
                    if (!visited.has(next)) {
                        visited.add(next);
                        queue.push([next, [...path, edge]]);
                    }
                }
            }
        }
        
        // Fallback: Permitir sobrecarga se no modo Fácil ou se não houver opção
        // (Will optimize this in next iterations)
        return null;
    }

    render() {
        const { ctx, canvas } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw Edges
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
            
            // Info box on cable
            if (this.powerOn) {
                const mx = (e.n1.x + e.n2.x) / 2;
                const my = (e.n1.y + e.n2.y) / 2;
                ctx.fillStyle = "rgba(0,0,0,0.6)";
                ctx.fillRect(mx - 20, my - 10, 40, 20);
                ctx.fillStyle = "white";
                ctx.font = "bold 10px Arial";
                ctx.textAlign = "center";
                ctx.fillText(`${e.carga_atual}/${e.capacidade_maxima}`, mx, my + 4);
            }
        });

        // Draw Nodes
        this.nodes.forEach(n => {
            ctx.fillStyle = COLORS.bg;
            ctx.strokeStyle = n.color;
            ctx.lineWidth = 3;
            
            if (n.type === 'gerador') {
                ctx.fillRect(n.x - 30, n.y - 30, 60, 60);
                ctx.strokeRect(n.x - 30, n.y - 30, 60, 60);
                ctx.fillStyle = "white";
                ctx.font = "bold 12px Arial";
                ctx.textAlign = "center";
                ctx.fillText("GEN", n.x, n.y - 5);
                ctx.fillText(`${n.energy_atual}/${n.capacidade_maxima}`, n.x, n.y + 15);
            } else if (n.type === 'cidade') {
                ctx.beginPath();
                ctx.moveTo(n.x, n.y - 30);
                ctx.lineTo(n.x + 30, n.y);
                ctx.lineTo(n.x + 20, n.y + 25);
                ctx.lineTo(n.x - 20, n.y + 25);
                ctx.lineTo(n.x - 30, n.y);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
                ctx.fillStyle = "white";
                ctx.textAlign = "center";
                ctx.fillText(`${n.energy_atual}/${n.demanda}`, n.x, n.y + 5);
            } else {
                ctx.beginPath();
                ctx.arc(n.x, n.y, 25, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
                ctx.fillStyle = "white";
                ctx.fillText("SUB", n.x, n.y + 5);
            }
            
            if (this.selectedNode === n) {
                ctx.strokeStyle = "white";
                ctx.setLineDash([5, 5]);
                ctx.strokeRect(n.x - 40, n.y - 40, 80, 80);
                ctx.setLineDash([]);
            }
        });
    }

    resetLevel() {
        this.buildLevel();
    }

    showHelp() {
        document.getElementById('help-modal').classList.remove('hidden');
        document.getElementById('help-text').innerHTML = `
            <p>1. <b>Conecte Nós:</b> Clique em um gerador e depois em uma subestação ou cidade para criar um cabo.</p>
            <p>2. <b>Distribuição:</b> Ligue a rede para ver a carga percorrendo o grid.</p>
            <p>3. <b>Sobrecarga:</b> Se o cabo ficar vermelho, ele está acima do limite. Use rotas paralelas!</p>
        `;
    }
}

let game;
function startGame(mode) {
    if (!game) game = new Game();
    game.startGame(mode);
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// Global start
window.onload = () => {
    // Menu is visible by default
};
