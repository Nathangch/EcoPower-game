import tkinter as tk
from tkinter import messagebox
import collections
import math
import random
import time

class WorldState:
    def __init__(self):
        self.time = 0.35 # 0.0 to 1.0 (midday at 0.5)
        self.wind = 0.5
        self.water = 0.8
        self.last_update = time.time()
        
    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        # Cycle time: 1 minute per day for testing
        self.time = (self.time + dt / 60.0) % 1.0
        # Random wind fluctuation
        self.wind = max(0.1, min(1.0, self.wind + random.uniform(-0.05, 0.05)))

class Node:
    def __init__(self, x, y, name, type_name, capacity=0):
        self.x = x
        self.y = y
        self.name = name
        self.type = type_name
        self.energy_atual = 0
        self.capacidade_maxima = capacity
        self.demanda = 0
        self.active = True
        self.radius = 35
        self.cost_paid = 0

class Generator(Node):
    def __init__(self, x, y, name, capacity, gen_type="PADRAO"):
        super().__init__(x, y, name, "gerador", capacity)
        self.gen_type = gen_type # TERMELETRICA, HIDRELETRICA, SOLAR, EOLICA, NUCLEAR
        self.thermal_risk = 0 # For nuclear/thermal overloads
        self.update_stats()

    def update_stats(self):
        if self.gen_type == "SOLAR": self.color = "#EBCB8B"
        elif self.gen_type == "EOLICA": self.color = "#88C0D0"
        elif self.gen_type == "HIDRELETRICA": self.color = "#5E81AC"
        elif self.gen_type == "TERMELETRICA": self.color = "#4C566A"
        elif self.gen_type == "NUCLEAR": self.color = "#BF616A"
        else: self.color = "#D08770"

class BatteryNode(Node):
    def __init__(self, x, y, name, max_storage=100):
        super().__init__(x, y, name, "bateria", 20) # 20 is max discharge rate
        self.max_storage = max_storage
        self.stored_energy = 0
        self.color = "#A3BE8C"
        self.charging = False

class Substation(Node):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "subestacao", 0)
        self.radius = 30
        self.color = "#88C0D0" # Light blueish

class City(Node):
    def __init__(self, x, y, name, demand):
        super().__init__(x, y, name, "cidade", 0)
        self.demanda = demand
        self.radius = 45
        self.color = "#81A1C1"

class Edge:
    def __init__(self, node1, node2, max_cap, cable_type="ALUMINIO"):
        self.n1 = node1
        self.n2 = node2
        self.capacidade_maxima = max_cap
        self.carga_atual = 0
        self.failed = False
        self.cable_type = cable_type # ALUMINIO, COBRE
        self.cost_paid = 0
        
    def get_other(self, node):
        return self.n2 if self.n1 == node else self.n1

class Poste(Node):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "poste")
        self.color = "#81A1C1"

class GameState:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.world = WorldState()
        self.difficulty = "Médio"  # Fácil, Médio, Difícil
        self.state = "RUNNING" # RUNNING, WIN, BOSS_BLACKOUT
        self.power_on = False
        self.current_level = 1
        self.mode = "EDUCACIONAL" # "EDUCACIONAL", "SUSTENTAVEL", "CRIATIVO"
        self.creative_item = "Cabo Baixa"
        self.money = 0
        self.build_initial_level()
        
    def build_initial_level(self):
        self.nodes.clear()
        self.edges.clear()
        self.state = "RUNNING"
        self.power_on = False

        if self.mode == "SUSTENTAVEL":
            self.money = 500 + (self.current_level * 150)
        
        if self.mode == "CRIATIVO":
            # Creative mode starts with an empty grid
            return
        
        diff = self.difficulty
        lvl = self.current_level
        
        # New logic for num_g, num_s, num_c and generator types
        if diff == "Fácil":
            num_g = 1 + (lvl // 6)
            num_s = 2 + (lvl // 4)
            num_c = 1 + (lvl // 5)
        elif diff == "Médio":
            num_g = 2 + (lvl // 6)
            num_s = 2 + (lvl // 3)
            num_c = 2 + (lvl // 4)
        else: # Difícil
            num_g = 2 + (lvl // 5)
            num_s = 3 + (lvl // 3)
            num_c = 3 + (lvl // 4)
            
        # Determine generator types for Sustainable mode
        gen_types = ["PADRAO"] * num_g
        if self.mode == "SUSTENTAVEL":
            types_pool = ["SOLAR", "EOLICA", "HIDRELETRICA", "TERMELETRICA"]
            gen_types = [random.choice(types_pool) for _ in range(num_g)]
            
        gens = [12 + random.randint(0, 8) for _ in range(num_g)] # Capacity for generators
        cities = [8 + random.randint(0, 12) for _ in range(num_c)] # Demand for cities
        
        # Ensure total generation is at least equal to total demand
        total_gen = sum(gens)
        total_dem = sum(cities)
        if total_gen < total_dem:
            # Adjust the last generator to cover the gap
            gens[-1] += (total_dem - total_gen)
            
        # Level 10 Boss Generation Logic
        if lvl == 10 and self.mode == "EDUCACIONAL":
            if diff == "Fácil": # Boss 1: Sobrecarga Simples
                # 2 Generators (30 each), 1 City (50 demand)
                # Goal: Force player to use multiple parallel cables (cap 20 each)
                self.nodes.append(Generator(150, 300, "Gerador Alpha", 30, "PADRAO"))
                self.nodes.append(Generator(150, 450, "Gerador Beta", 30, "PADRAO"))
                self.nodes.append(City(850, 375, "Metrópole", 50))
                return
            elif diff == "Médio": # Boss 3: Fluxo Caótico
                # 2 Generators, 3 substations, 2 cities
                # Distance based loss already handled in distribution, just need a spread layout
                self.nodes.append(Generator(100, 150, "Gerador 1", 30, "PADRAO"))
                self.nodes.append(Generator(100, 500, "Gerador 2", 30, "PADRAO"))
                self.nodes.append(Substation(400, 325, "Sub Central"))
                self.nodes.append(Substation(600, 150, "Sub Norte"))
                self.nodes.append(Substation(600, 550, "Sub Sul"))
                self.nodes.append(City(900, 200, "Cidade Norte", 25))
                self.nodes.append(City(900, 500, "Cidade Sul", 25))
                return
            elif diff == "Difícil": # Boss 6: IA da Rede
                # 3 Generators, 4 Substations, 3 Cities.
                # Redundancy (N-1) is key here.
                for i in range(3):
                    self.nodes.append(Generator(100, 150+i*200, f"G{i+1}", 40, "PADRAO"))
                    self.nodes.append(City(900, 150+i*200, f"C{i+1}", 30))
                for i in range(4):
                    self.nodes.append(Substation(500, 100+i*150, f"S{i+1}"))
                return

        # Normal Level Generation
        for i, cap in enumerate(gens):
            x = random.randint(80, 200)
            y = 100 + (500 // max(1, num_g)) * i + random.randint(-15, 15)
            self.nodes.append(Generator(x, y, f"Gerador {i+1}", cap, gen_types[i]))
            
        for i in range(num_s):
            x = random.randint(350, 650)
            y = 100 + (500 // max(1, num_s)) * i + random.randint(-30, 30)
            self.nodes.append(Substation(x, y, f"Sub {chr(65+i)}"))
            
        for i, dem in enumerate(cities):
            x = random.randint(780, 920)
            y = 100 + (500 // max(1, num_c)) * i + random.randint(-20, 20)
            self.nodes.append(City(x, y, f"Cidade {i+1}", dem))
            
        # Overlap separation pass
        for _ in range(10):
            for n1 in self.nodes:
                for n2 in self.nodes:
                    if n1 != n2:
                        dist = math.hypot(n1.x - n2.x, n1.y - n2.y)
                        min_dist = n1.radius + n2.radius + 15
                        if dist < min_dist and dist > 0:
                            n1.y += 10 if n1.y > n2.y else -10

    def get_item_price(self, item_name):
        prices = {
            "Solar": 200, "Eólico": 180, "Carvão": 150, "Termelétrica": 170, "Nuclear": 300, "Hidrelétrica": 250,
            "Subestação": 150, "Poste": 20, "Transformador": 50, "Bateria": 100,
            "Cid. Pequena": 0, "Cid. Grande": 0, # Cities are usually given, not bought
            "Cabo Baixa": 5, "Cabo Média": 15, "Cabo Alta": 40, "Supercondutor": 100,
            "Alicate": 0, "Medidor Carga": 0, "Detector Falhas": 0
        }
        return prices.get(item_name, 0)

    def update_flow(self):
        if not self.power_on:
            for n in self.nodes: n.energy_atual = 0
            for e in self.edges: e.carga_atual = 0
            return

        if self.mode != "EDUCACIONAL":
            self.world.update()
        
        # Calculate Current available Capacities based on World State
        for n in self.nodes:
            if n.type == "gerador":
                base = n.capacidade_maxima
                if n.gen_type == "SOLAR" and self.mode != "EDUCACIONAL":
                    # Midday (0.5) is peak; Night (0.0 or 0.7+) is 0
                    mult = max(0, math.sin((self.world.time - 0.25) * 2 * math.pi))
                    n.capacidade_atual = base * mult
                elif n.gen_type == "EOLICA" and self.mode != "EDUCACIONAL":
                    n.capacidade_atual = base * self.world.wind
                elif n.gen_type == "HIDRELETRICA" and self.mode != "EDUCACIONAL":
                    n.capacidade_atual = base * self.world.water
                else:
                    n.capacidade_atual = base
                n.energy_atual = 0 # Reset for BFS
            elif n.type == "bateria":
                # Battery acts as a generator if it has charge
                n.capacidade_atual = min(n.capacidade_maxima, n.stored_energy)
                n.energy_atual = 0
            else:
                n.energy_atual = 0

        if self.state == "BOSS_BLACKOUT":
            return
            
        if not self.power_on:
            for e in self.edges: e.carga_atual = 0
            for n in self.nodes: n.energy_atual = 0
            return
            
        loop_safe_guard = 0
        while True:
            self._distribute_energy()
            failed = self._check_failures()
            
            self._check_boss_condition()
            
            if not failed or self.state == "BOSS_BLACKOUT":
                break
                
            loop_safe_guard += 1
            if loop_safe_guard > 50:
                print("Warning: Infinite collapse loop broke")
                break
                
        self._check_win()

    def _distribute_energy(self):
        for e in self.edges: 
            e.carga_atual = 0
        for n in self.nodes:
            n.energy_atual = 0
            
        # 3. Handle Batteries and Storage
        # Step A: Check for excess energy to charge batteries
        total_gen = sum(n.capacidade_atual for n in self.nodes if n.type == "gerador")
        total_dem = sum(n.demanda for n in self.nodes if n.type == "cidade")
        
        excess = max(0, total_gen - total_dem)
        batteries = [n for n in self.nodes if n.type == "bateria"]
        
        if excess > 0 and batteries and self.mode != "EDUCACIONAL":
            charge_per = excess / len(batteries)
            for b in batteries:
                b.stored_energy = min(b.max_storage, b.stored_energy + charge_per * 0.1) # slow charge
                b.charging = True
        else:
            for b in batteries: b.charging = False

        # ... (rest of BFS remains or is updated to use n.capacidade_atual)
        # Actually, let's keep the existing flow logic but ensure it uses the prioritized ordered_sources
        # Prioritize generators with higher capacity or specific types
        ordered_sources = sorted([n for n in self.nodes if n.type == "gerador" or n.type == "bateria"], 
                                 key=lambda n: n.capacidade_atual, reverse=True)
        
        # Propagação contínua de 1 em 1 unidade de energia para cidades
        while True:
            power_moved = False
            for source in ordered_sources:
                if source.energy_atual < source.capacidade_atual: # Use capacidade_atual
                    path = self.find_path(source, allow_overload=False)
                    
                    if not path:
                        path = self.find_path(source, allow_overload=True)
                        
                    if path:
                        source.energy_atual += 1
                        current = source
                        for edge in path:
                            edge.carga_atual += 1
                            current = edge.get_other(current)
                            
                        # BOSS 3: Fluxo Caótico (Energy Loss based on path length)
                        reached = True
                        if self.difficulty == "Médio" and self.current_level == 10:
                            loss_prob = max(0, (len(path) - 3) * 0.25) # 25% loss per node over 3
                            if random.random() < loss_prob:
                                reached = False
                                
                        if reached:
                            current.energy_atual += 1
                        else:
                            # Energy lost in transit - maybe show a message one time?
                            pass
                            
                        power_moved = True
            if not power_moved:
                break
                
    def find_path(self, start_gen, allow_overload=False):
        queue = collections.deque([(start_gen, [])])
        visited = {start_gen}
        
        while queue:
            current, path = queue.popleft()
            
            if current.type == "cidade" and current.energy_atual < current.demanda:
                return path
            
            edges = [e for e in self.edges if e.n1 == current or e.n2 == current]
            for edge in edges:
                if edge.failed: continue
                
                # Try to find paths that are not overloaded first
                # Try to find paths that are not overloaded first
                if not allow_overload and edge.carga_atual >= edge.capacidade_maxima:
                    continue
                    
                nxt = edge.get_other(current)
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [edge]))
        return None

    def _check_failures(self):
        if self.difficulty == "Fácil": 
            # BOSS 1 EVENT: Load limit ACTIVE in Level 10
            if self.current_level < 10:
                return False
            # If Level 10, proceed to overload logic (behaves like Medium mode)
            
        overloaded = [e for e in self.edges if e.carga_atual > e.capacidade_maxima and not e.failed]
        if overloaded:
            # Medium, or Easy Level 10 Boss
            if self.difficulty == "Médio" or (self.difficulty == "Fácil" and self.current_level == 10):
                # Fail one edge
                e = overloaded[0]
                e.failed = True
                return True
                
            elif self.difficulty == "Difícil":
                # Cascading: all overloads fail together, triggering loop
                for e in overloaded:
                    e.failed = True
                return True
        return False
        
    def _check_boss_condition(self):
        if self.state == "BOSS_BLACKOUT" or self.difficulty != "Difícil": return
        
        # If no energy is reaching any cities but demand exists, and at least one failure happened
        total_delivered = sum(c.energy_atual for c in self.nodes if c.type == "cidade")
        any_failed = any(e.failed for e in self.edges)
        
        if total_delivered == 0 and any_failed:
            self.state = "BOSS_BLACKOUT"

    def _check_win(self):
        if self.state == "BOSS_BLACKOUT" or self.mode == "CRIATIVO": return
        
        all_satisfied = all(c.energy_atual >= c.demanda for c in self.nodes if c.type == "cidade")
        no_overloads = all(e.carga_atual <= e.capacidade_maxima for e in self.edges)
        
        if all_satisfied and no_overloads:
            self.state = "WIN"
        elif self.state == "WIN":
            self.state = "RUNNING" # Back to running if broken
            
    def get_sustainability_index(self):
        if self.mode != "SUSTENTAVEL": return 100
        total_gen_capacity = sum(n.capacidade_maxima for n in self.nodes if n.type == "gerador")
        if total_gen_capacity == 0: return 100
        
        coal_gen_capacity = sum(n.capacidade_maxima for n in self.nodes if n.type == "gerador" and n.gen_type == "CARVAO")
        # Simple formula: 100% - % generated by coal
        index = 100 - (100 * coal_gen_capacity // total_gen_capacity)
        return index

    def get_victory_message(self):
        messages = [
            # 1-5: Basic Concepts
            "Excelente! Você conectou seu primeiro gerador. Em um circuito elétrico básico, a eletricidade sempre percorre o caminho de menor resistência. Ao conectar o gerador à cidade, você 'fechou' o circuito, permitindo que a energia flua e realize o trabalho necessário para acender as luzes.",
            "Muito bem! Ao usar subestações, você começou a organizar o fluxo. Na engenharia, subestações servem para 'concentrar' e redirecionar a energia vinda de fontes distantes, permitindo que o grid seja expandido para áreas onde geradores não podem ser construídos diretamente.",
            "Ótimo! Você percebeu que geradores podem somar suas forças. É como ligar duas baterias em paralelo no mesmo rádio: a voltagem continua a mesma, mas a 'capacidade' total de suprir energia aumenta, permitindo alimentar cidades com demandas bem maiores.",
            "Sabia que a ordem das conexões importa? Ao criar uma rede estável, você evitou que a energia ficasse 'presa' apenas em um gerador. O equilíbrio da geração é vital para que nenhum equipamento trabalhe sob estresse constante, prolongando a vida útil da rede.",
            "Incrível! Você concluiu a introdução básica. Agora você já sabe que a eletricidade viaja da Fonte (Gerador) para o Consumo (Cidade) e que nós intermediários (Subestações) ajudam a gerenciar essa jornada sem desperdiçar potencial energético.",
            
            # 6-10: Parallel Paths and Load Balancing
            "Atenção Técnica: Aqui você usou circuitos paralelos! Quando a demanda (9 MW) supera a carga do cabo (8 MW), você 'divide' o fluxo em dois caminhos. Isso reduz a 'fricção' nos fios, evitando o Efeito Joule (superaquecimento) que derreteria o isolamento metálico.",
            "Redundância: Você criou o que chamamos de 'Malha em Anel'. No mundo real, se um desses cabos rompesse, a energia ainda teria um caminho alternativo para chegar na cidade. Isso é o que impede que um bairro inteiro fique no escuro quando um carro bate em um poste.",
            "Equilíbrio de Carga: Você distribuiu a energia entre as subestações. Se uma subestação recebesse todo o peso sozinha, ela se tornaria um 'Ponto Único de Falha'. Sua estratégia de diversificar as rotas torna o sistema muito mais resiliente e seguro.",
            "Drenagem Térmica: A eletricidade gera calor ao passar por condutores. Ao escolher rotas inteligentes, você garantiu que nenhum cabo atingisse o ponto crítico de 100% de uso. Manter uma margem de segurança (folga) é a regra de ouro do engenheiro eletrotécnico.",
            "Domínio Urbano: Cidades grandes agora estão seguras! Ao alimentar as metrópoles por múltiplos pontos (alimentação multifeeder), você garantiu que a alta demanda não causasse quedas de tensão no final da linha.",
            
            # 11-15: Reliability and Grid Redundancy
            "Gerenciamento de Pico: Você distribuiu o esforço de geradores potentes. Em horários de pico (como às 18h), um engenheiro precisa antecipar onde a carga será maior e preparar 'caminhos de escape' para a energia extra não saturar o centro da cidade.",
            "Arquitetura em Estrela: Usar uma subestação central para vários destinos facilita o monitoramento. Na engenharia de redes, isso centraliza o controle e permite que você isole rapidamente um curto-circuito em apenas uma ramificação, sem derrubar as outras.",
            "Eficiência Magnética: Você evitou gargalos. Quando muitos elétrons tentam passar por um cabo fino ao mesmo tempo, a 'resistência' aumenta, e muita energia se perde em forma de calor. Sua rede de várias vias minimiza essa perda financeira e energética.",
            "Setorização: Ao separar áreas industriais de áreas residenciais através de subestações dedicadas, você evitou que uma sobrecarga em uma fábrica desligasse o hospital da cidade vizinha. A separação lógica é vital no planejamento urbano.",
            "Ponto de Entrega (Subtransmissão): Você atingiu a metade do caminho! O uso de subestações intermediárias permitiu que o sistema 'descansasse' antes de entregar a carga final, garantindo que a voltagem chegasse estabilizada nas tomadas dos moradores.",
            
            # 16-20: Urban Complexity and High Demand
            "Estabilidade do Sistema: Adicionar novos geradores em uma malha ativa exige cuidado. Você soube integrar a nova geração sem desequilibrar a carga que já existia. É como trocar a roda de um carro em movimento no setor elétrico.",
            "Manutenção Preventiva Geográfica: Você levou energia para pontos distantes. Cabos muito longos perdem voltagem natural (queda de tensão). Ao usar estações de apoio no meio do caminho, você 'reforçou' a qualidade da entrega elétrica.",
            "Sobrecarga Controlada: No modo fácil ou difícil, o princípio é o mesmo: a infraestrutura tem limites. Você provou que entende que a economia de cabos (usar só um) gera um risco inaceitável de blackout no futuro econômico da sua cidade.",
            "Otimização de Fluxo (Power Flow): A energia elétrica não escolhe o caminho que você quer, ela escolhe o caminho mais fácil (menor reatância). Sua maestria foi forçar esse caminho a ser seguro através de rotas alternativas bem desenhadas.",
            "Resiliência sob Estresse: Mesmo com as cidades 'puxando' o máximo de carga, sua rede se manteve equilibrada. Um sistema estável é aquele que opera de forma silenciosa e eficiente, sem que o consumidor perceba o esforço térmico por trás.",
            
            # 21-25: Advanced Management
            "Sistemas de Grande Porte: Você gerenciou múltiplas fontes e consumidores ao mesmo tempo. A sincronia entre a geração disponível e a demanda consumida é o maior desafio do Operador Nacional do Sistema Elétrico (ONS) no Brasil.",
            "Smart Grids (Redes Inteligentes): No futuro, medidores inteligentes avisam onde haverá consumo máximo. Hoje, você fez esse papel manualmente, antecipando os gargalos e reforçando a malha antes de sequer ligar os disjuntores centrais.",
            "Segurança de N-1: Este conceito diz que o sistema deve continuar operando se UMA conexão falhar. Sua vitória hoje mostrou que você construiu uma rede capaz de sobreviver a imprevistos técnicos e manter a ordem pública.",
            "Engenharia de Proteção: O layout complexo que você resolveu exigiu visão espacial. É necessário ver o grid como um todo, não apenas como fios isolados. Cada conexão altera o destino da energia em toda a rede ao redor.",
            "Mestre da Engenharia de Sistemas: Parabéns! Você domina todos os conceitos de geração, subtransmissão e distribuição final. Você está pronto para projetar grades elétricas seguras, eficientes e preparadas para o futuro da sociedade!"
        ]
        if self.current_level <= len(messages):
            return messages[self.current_level - 1]
        return "Parabéns por completar este desafio de engenharia!"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EcoPower - Distribuição de Energia")
        self.geometry("1320x820")
        self.configure(bg="#2E3440")
        
        self.game = GameState()
        self.selected_node = None
        self.current_frame = None
        self.victory_shown = False
        
        # Labels for dynamic updates
        self.lbl_fase = None
        self.lbl_sus = None
        self.lbl_money = None
        
        self.flash_state = True
        self.sabotage_timer = 20 # 10 seconds (20 * 500ms)
        self.after(500, self.flash_loop)
        
        self.show_menu()

    def show_menu(self):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = tk.Label(self.current_frame, text="EcoPower", bg="#2E3440", fg="#EBCB8B", font=("Arial", 48, "bold"))
        lbl_title.pack(pady=(80, 20))
        
        btn_start = tk.Button(self.current_frame, text="Iniciar Jogo", command=self.show_mode_selection, bg="#A3BE8C", fg="#2E3440", font=("Arial", 18, "bold"), width=15, relief="flat", cursor="hand2")
        btn_start.pack(pady=10)
        
        btn_tut = tk.Button(self.current_frame, text="Como Jogar", command=self.show_tutorial, bg="#EBCB8B", fg="#2E3440", font=("Arial", 18, "bold"), width=15, relief="flat", cursor="hand2")
        btn_tut.pack(pady=10)
        
        btn_quit = tk.Button(self.current_frame, text="Fechar Jogo", command=self.destroy, bg="#BF616A", fg="#ECEFF4", font=("Arial", 18, "bold"), width=15, relief="flat", cursor="hand2")
        btn_quit.pack(pady=10)

    def show_mode_selection(self):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = tk.Label(self.current_frame, text="Selecione o Modo de Jogo", bg="#2E3440", fg="#EBCB8B", font=("Arial", 36, "bold"))
        lbl_title.pack(pady=(80, 40))
        
        btn_educacional = tk.Button(self.current_frame, text="EDUCACIONAL", command=lambda: self.set_mode_and_continue("EDUCACIONAL"), bg="#A3BE8C", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_educacional.pack(pady=5)
        lbl_educacional = tk.Label(self.current_frame, text="Aprenda os conceitos básicos de redes elétricas.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_educacional.pack(pady=(0, 15))
        
        btn_sustentavel = tk.Button(self.current_frame, text="SUSTENTÁVEL", command=lambda: self.set_mode_and_continue("SUSTENTAVEL"), bg="#88C0D0", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_sustentavel.pack(pady=5)
        lbl_sustentavel = tk.Label(self.current_frame, text="Construa uma rede com fontes de energia renováveis.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_sustentavel.pack(pady=(0, 15))
        
        btn_criativo = tk.Button(self.current_frame, text="CRIATIVO", command=lambda: self.set_mode_and_continue("CRIATIVO"), bg="#EBCB8B", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_criativo.pack(pady=5)
        lbl_criativo = tk.Label(self.current_frame, text="Crie sua própria rede do zero.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_criativo.pack(pady=(0, 15))
        
        btn_back = tk.Button(self.current_frame, text="Voltar", command=self.show_menu, bg="#4C566A", fg="#ECEFF4", font=("Arial", 14), width=15, relief="flat", cursor="hand2")
        btn_back.pack(pady=20)

    def set_mode_and_continue(self, mode):
        self.game.mode = mode
        if mode in ["CRIATIVO", "SUSTENTAVEL"]:
            self.game.nodes.clear()
            self.game.edges.clear()
            self.show_game()
        else:
            self.show_difficulty_selection()

    def show_tutorial(self):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = tk.Label(self.current_frame, text="Como Jogar", bg="#2E3440", fg="#EBCB8B", font=("Arial", 36, "bold"))
        lbl_title.pack(pady=(60, 20))
        
        tutorial_text = (
            "1. GERADORES E CIDADES:\n"
            "   Os Geradores (Amarelos) produzem energia, e as Cidades (Casas) consomem.\n"
            "   O seu objetivo é suprir a demanda exata de todas as cidades da rede.\n\n"
            "2. REDE ELÉTRICA INTERLIGADA (GRID):\n"
            "   Um gerador sozinho pode não ser suficiente para abastecer uma cidade grande!\n"
            "   Conecte múltiplos geradores à mesma malha (usando as Subestações) para\n"
            "   somar as energias no grid e conseguir abastecer as cidades maiores.\n\n"
            "3. LIMITES DE CABO E EFEITO CASCATA:\n"
            "   Atenção: no modo Fácil, o cabo aguenta 8⚡. No Médio/Difícil, apenas 5⚡.\n"
            "   Se uma cidade precisa de carga extra, você precisará puxar linhas paralelas de \n"
            "   subestações diferentes para ela, para dividir a carga e não estourar os fios!"
        )
        
        lbl_tut = tk.Label(self.current_frame, text=tutorial_text, bg="#2E3440", fg="#ECEFF4", font=("Arial", 16), justify="left")
        lbl_tut.pack(pady=20)
        
        btn_back = tk.Button(self.current_frame, text="Entendi!", command=self.show_menu, bg="#A3BE8C", fg="#2E3440", font=("Arial", 16, "bold"), width=15, relief="flat", cursor="hand2")
        btn_back.pack(pady=30)

    def show_difficulty_selection(self):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = tk.Label(self.current_frame, text="Selecione a Dificuldade", bg="#2E3440", fg="#EBCB8B", font=("Arial", 36, "bold"))
        lbl_title.pack(pady=(80, 40))
        
        btn_facil = tk.Button(self.current_frame, text="FÁCIL", command=lambda: self.start_game_with_diff("Fácil"), bg="#A3BE8C", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_facil.pack(pady=5)
        lbl_facil = tk.Label(self.current_frame, text="Limites de carga ignorados.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_facil.pack(pady=(0, 15))
        
        btn_medio = tk.Button(self.current_frame, text="MÉDIO", command=lambda: self.start_game_with_diff("Médio"), bg="#EBCB8B", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_medio.pack(pady=5)
        lbl_medio = tk.Label(self.current_frame, text="Falhas isoladas ocorrem com sobrecarga.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_medio.pack(pady=(0, 15))
        
        btn_dificil = tk.Button(self.current_frame, text="DIFÍCIL", command=lambda: self.start_game_with_diff("Difícil"), bg="#BF616A", fg="#2E3440", font=("Arial", 16, "bold"), width=20, relief="flat", cursor="hand2")
        btn_dificil.pack(pady=5)
        lbl_dificil = tk.Label(self.current_frame, text="Efeito cascata. Risco de Apagão Geral.", bg="#2E3440", fg="#ECEFF4", font=("Arial", 11))
        lbl_dificil.pack(pady=(0, 15))
        
        btn_back = tk.Button(self.current_frame, text="Voltar", command=self.show_mode_selection, bg="#4C566A", fg="#ECEFF4", font=("Arial", 14), width=15, relief="flat", cursor="hand2")
        btn_back.pack(pady=20)
        
    def start_game_with_diff(self, diff):
        self.game.difficulty = diff
        self.game.current_level = 1
        self.show_pre_game_tip(diff)
        
    def show_pre_game_tip(self, diff):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        msg = ""
        if diff == "Fácil":
            msg = "⚡ MODO FÁCIL ⚡\n\nVocê tem liberdade total para conectar os nós sem se\npreocupar com limites de carga física nos cabos."
        elif diff == "Médio":
            msg = "⚡ MODO MÉDIO ⚡\n\nAtenção à Carga!\nSe a energia fluindo no cabo exceder a capacidade máxima (5 ⚡),\nele irá se romper e você precisará refazer a arquitetura."
        else:
            msg = "⚡ MODO DIFÍCIL ⚡\n\nCuidado Extremo!\nUma linha sobrecarregada irá se romper e a energia será\nredirecionada para outras linhas automaticamente...\no que pode causar um Efeito Cascata e um Apagão Geral na rede!"

        lbl_title = tk.Label(self.current_frame, text="Dica Importante da Fase", bg="#2E3440", fg="#EBCB8B", font=("Arial", 36, "bold"))
        lbl_title.pack(pady=(100, 30))
        
        lbl_tip = tk.Label(self.current_frame, text=msg, bg="#2E3440", fg="#ECEFF4", font=("Arial", 18), justify="center")
        lbl_tip.pack(pady=20)
        
        btn_start = tk.Button(self.current_frame, text="Começar Simulação", command=self.show_game, bg="#A3BE8C", fg="#2E3440", font=("Arial", 18, "bold"), width=20, relief="flat", cursor="hand2")
        btn_start.pack(pady=40)
        
    def show_game(self):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        if self.game.mode != "CRIATIVO": # Only build initial level if not creative mode
            self.game.build_initial_level()
            
        # Check for Boss Events
        self.check_boss_event()
            
        self.selected_node = None
        self.game.power_on = False # Initialize power state
        self.victory_shown = False
        
        self.setup_ui()
        self.draw_grid()
        
        # Check for Boss Events AFTER UI is setup
        self.after(1000, self.check_boss_event)

    def setup_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        
        self.current_frame = tk.Frame(self, bg="#2E3440")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top Panel (Directly in current_frame)
        top_frame = tk.Frame(self.current_frame, bg="#3B4252", height=70)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        btn_menu = tk.Button(top_frame, text="⮌ Menu", command=self.show_menu, bg="#4C566A", fg="#ECEFF4", font=("Arial", 12, "bold"), relief="flat", cursor="hand2")
        btn_menu.pack(side=tk.LEFT, padx=10, pady=15)
        
        self.btn_power = tk.Button(top_frame, text="▶ LIGAR REDE", command=self.toggle_power, bg="#A3BE8C", fg="#2E3440", font=("Arial", 12, "bold"), relief="flat", cursor="hand2", padx=10)
        self.btn_power.pack(side=tk.LEFT, padx=10, pady=15)
        
        self.lbl_info = tk.Label(top_frame, text="Info: Planeje a rede", bg="#3B4252", fg="#ECEFF4", font=("Arial", 12, "bold"))
        self.lbl_info.pack(side=tk.LEFT, padx=20)
        
        # Right info section
        btn_reset = tk.Button(top_frame, text="Reset Nível", command=self.reset_level, bg="#BF616A", fg="#ECEFF4", font=("Arial", 11, "bold"), relief="flat", cursor="hand2")
        btn_reset.pack(side=tk.RIGHT, padx=10, pady=15)
        
        if self.game.mode != "CRIATIVO":
            lbl_diff = tk.Label(top_frame, text=f"Dificuldade: {self.game.difficulty.upper()}", bg="#3B4252", fg="#EBCB8B", font=("Arial", 13, "bold"))
            lbl_diff.pack(side=tk.RIGHT, padx=20)
        
        # Sustainability & Money
        if self.game.mode == "SUSTENTAVEL":
            sus_idx = self.game.get_sustainability_index()
            self.lbl_sus = tk.Label(top_frame, text=f"Sustentabilidade: {sus_idx}%", bg="#3B4252", fg="#A3BE8C" if sus_idx > 70 else "#BF616A", font=("Arial", 12, "bold"))
            self.lbl_sus.pack(side=tk.RIGHT, padx=20)
            self.lbl_money = tk.Label(top_frame, text=f"Orçamento: ${self.game.money}", bg="#3B4252", fg="#EBCB8B", font=("Arial", 14, "bold"))
            self.lbl_money.pack(side=tk.RIGHT, padx=20)
        else:
            self.lbl_sus = None
            self.lbl_money = None
        
        if self.game.mode in ["EDUCACIONAL", "SUSTENTAVEL"]:
            self.lbl_fase = tk.Label(top_frame, text=f"FASE {self.game.current_level}/10", bg="#3B4252", fg="#A3BE8C", font=("Arial", 14, "bold"))
            self.lbl_fase.pack(side=tk.RIGHT, padx=20)
        elif self.game.mode == "CRIATIVO":
            lbl_mode = tk.Label(top_frame, text="MODO CRIATIVO", bg="#3B4252", fg="#88C0D0", font=("Arial", 14, "bold"))
            lbl_mode.pack(side=tk.RIGHT, padx=20)
            self.lbl_fase = None
        
        # Body (Sidebar + Canvas)
        body = tk.Frame(self.current_frame, bg="#2E3440")
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        if self.game.mode in ["CRIATIVO", "SUSTENTAVEL"]:
            self.setup_creative_sidebar(body)
            
        # Canvas
        self.canvas = tk.Canvas(body, bg="#2E3440", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Configure>", lambda e: self.draw_grid()) # Redraw on resize
        
        # Help Button - Responsive placement relative to canvas
        if self.game.mode in ["EDUCACIONAL", "SUSTENTAVEL"]:
            txt = "? Como Jogar? (Educativo)" if self.game.mode == "EDUCACIONAL" else "G Guia de Sustentabilidade"
            self.btn_help = tk.Button(self.canvas, text=txt, command=self.show_help_overlay, 
                                     bg="#EBCB8B" if self.game.mode == "EDUCACIONAL" else "#A3BE8C", 
                                     fg="#2E3440", font=("Arial", 12, "bold"), padx=10, relief="raised", cursor="hand2")
            # Place it over the canvas at a consistent relative position
            self.btn_help.place(relx=0.5, rely=0.95, anchor=tk.S)

    def setup_creative_sidebar(self, parent):
        self.sidebar = tk.Frame(parent, bg="#3B4252", width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="INVENTÁRIO", bg="#3B4252", fg="#EBCB8B", font=("Arial", 12, "bold")).pack(pady=15)
        
        # Categories list
        self.categories = {
            "⚡ GERAÇÃO": ["Solar", "Eólico", "Carvão", "Termelétrica", "Nuclear", "Hidrelétrica"],
            "🔌 DISTRIB": ["Subestação", "Poste", "Transformador", "Bateria"],
            "🏘️ DEMANDA": ["Cid. Pequena", "Cid. Grande"],
            "🔗 FIAÇÃO": ["Cabo Baixa", "Cabo Média", "Cabo Alta", "Supercondutor"],
            "🧰 FERRAMENTAS": ["Medidor Carga", "Detector Falhas", "Alicate"]
        }
        
        # Category Buttons container
        cat_frame = tk.Frame(self.sidebar, bg="#2E3440")
        cat_frame.pack(fill=tk.X, padx=5)
        
        self.cat_btns = {}
        for cat in self.categories.keys():
            btn = tk.Button(cat_frame, text=cat, bg="#4C566A", fg="#D8DEE9", font=("Arial", 9, "bold"), 
                           command=lambda c=cat: self.show_category(c), relief="flat", pady=5)
            btn.pack(side=tk.TOP, fill=tk.X, pady=2)
            self.cat_btns[cat] = btn
            
        # Items container
        tk.Label(self.sidebar, text="--- Itens ---", bg="#3B4252", fg="#88C0D0", font=("Arial", 10)).pack(pady=10)
        self.item_frame = tk.Frame(self.sidebar, bg="#3B4252")
        self.item_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        self.show_category("⚡ GERAÇÃO") # Default category

    def show_category(self, cat_name):
        # Refresh buttons look
        for name, btn in self.cat_btns.items():
            if name == cat_name:
                btn.config(bg="#88C0D0", fg="#2E3440")
            else:
                btn.config(bg="#4C566A", fg="#D8DEE9")
                
        # Clear item frame
        for widget in self.item_frame.winfo_children():
            widget.destroy()
            
        # Add new item buttons
        self.item_buttons = {}
        for item in self.categories[cat_name]:
            display_text = item
            if self.game.mode == "SUSTENTAVEL":
                price = self.game.get_item_price(item)
                if price > 0:
                    display_text = f"{item} (${price})"
            
            btn = tk.Button(self.item_frame, text=display_text, bg="#434C5E", fg="#ECEFF4", font=("Arial", 11, "bold"),
                           command=lambda i=item: self.select_creative_item(i), relief="flat", pady=8)
            btn.pack(fill=tk.X, pady=4)
            self.item_buttons[item] = btn
            
        # Pre-select first item or current one if it belongs to this category
        if self.game.creative_item in self.categories[cat_name]:
            self.select_creative_item(self.game.creative_item)
        else:
            self.select_creative_item(self.categories[cat_name][0])


    def toggle_power(self):
        self.game.power_on = not self.game.power_on
        if self.game.power_on:
            self.btn_power.config(text="■ DESLIGAR REDE", bg="#BF616A", fg="#ECEFF4")
        else:
            self.btn_power.config(text="▶ LIGAR REDE", bg="#A3BE8C", fg="#2E3440")
        
        self.game.update_flow()
        self.draw_grid()

    def reset_level(self):
        saved_lvl = self.game.current_level
        saved_diff = self.game.difficulty
        saved_mode = self.game.mode

        if saved_mode == "CRIATIVO":
            self.game.nodes = []
            self.game.edges = []
        else:
            self.game.difficulty = saved_diff
            self.game.current_level = saved_lvl
            self.game.build_initial_level()
        
        if hasattr(self, 'btn_power'):
            self.btn_power.config(text="▶ LIGAR REDE", bg="#A3BE8C", fg="#2E3440")
        self.game.power_on = False # Reset power state
        self.victory_shown = False
        self.selected_node = None
        
        # Update labels if they exist
        if self.lbl_fase:
            self.lbl_fase.config(text=f"FASE {self.game.current_level}/10")
        if self.lbl_sus:
            sus_idx = self.game.get_sustainability_index()
            self.lbl_sus.config(text=f"Sustentabilidade: {sus_idx}%", fg="#A3BE8C" if sus_idx > 70 else "#BF616A")
        if self.lbl_money:
            self.lbl_money.config(text=f"Orçamento: ${self.game.money}")
                        
        self.draw_grid()

    def next_level(self):
        self.game.current_level += 1
        self.victory_shown = False
        self.reset_level()
        # Boss intro should be shown after level reset and UI update
        self.after(1000, self.check_boss_event)

    def check_boss_event(self):
        # Ensure we are in a running game state and on level 10
        if not hasattr(self, 'current_frame') or not self.current_frame.winfo_exists(): return
        
        if self.game.mode == "EDUCACIONAL" and self.game.current_level == 10:
            if self.game.difficulty == "Fácil":
                self.show_boss_intro()
            elif self.game.difficulty == "Médio":
                self.show_boss3_intro()
            elif self.game.difficulty == "Difícil":
                self.show_boss6_intro()

    def get_node_at(self, x, y):
        for n in self.game.nodes:
            if math.hypot(n.x - x, n.y - y) <= n.radius + 5:
                return n
        return None

    def get_edge_at(self, x, y):
        for e in self.game.edges:
            # Distance from point to line segment
            px, py = e.n1.x, e.n1.y
            qx, qy = e.n2.x, e.n2.y
            
            l2 = (px-qx)**2 + (py-qy)**2
            if l2 == 0: continue
            
            t = max(0, min(1, ((x-px)*(qx-px) + (y-py)*(qy-py)) / l2))
            proj_x = px + t*(qx-px)
            proj_y = py + t*(qy-py)
            
            if math.hypot(x - proj_x, y - proj_y) < 8:
                return e
        return None

    def on_left_click(self, event):
        x, y = event.x, event.y
        
        # Creative/Sustainable Mode - Tools & Place Item
        if self.game.mode in ["CRIATIVO", "SUSTENTAVEL"]:
            item = self.game.creative_item
            
            # Tools
            if item == "Alicate":
                clicked_node = self.get_node_at(x, y)
                if clicked_node:
                    self.game.edges = [e for e in self.game.edges if e.n1 != clicked_node and e.n2 != clicked_node]
                    self.game.nodes.remove(clicked_node)
                    self.draw_grid()
                    return
                for e in self.game.edges:
                    mx, my = (e.n1.x + e.n2.x) / 2, (e.n1.y + e.n2.y) / 2
                    if math.sqrt((x-mx)**2 + (y-my)**2) < 20:
                        self.game.edges.remove(e)
                        self.game.update_flow()
                        self.draw_grid()
                        return
                return
            
            if item == "Medidor Carga":
                target = self.get_node_at(x, y)
                if target:
                    val = target.energy_atual if hasattr(target, 'energy_atual') else 0
                    self.lbl_info.config(text=f"📊 Medição: {target.name} - Fluxo Atual: {int(val)} MW", fg="#A3BE8C")
                    return
                for e in self.game.edges:
                    mx, my = (e.n1.x + e.n2.x) / 2, (e.n1.y + e.n2.y) / 2
                    if math.sqrt((x-mx)**2 + (y-my)**2) < 20:
                        self.lbl_info.config(text=f"📊 Cabo: {int(e.carga_atual)}/{e.capacidade_maxima} MW", fg="#88C0D0")
                        return
                return
            
            if item == "Detector Falhas":
                critical = [e for e in self.game.edges if e.carga_atual >= e.capacidade_maxima]
                if critical:
                    self.lbl_info.config(text=f"⚠️ ALERTA: {len(critical)} cabos em sobrecarga!", fg="#BF616A")
                else:
                    self.lbl_info.config(text="✅ Sistema estável. Nenhuma falha detectada.", fg="#A3BE8C")
                self.draw_grid()
                return

            # Placement with Economy
            if "Cabo" not in item and item != "Supercondutor" and "Medidor" not in item and "Detector" not in item and "Alicate" not in item:
                if self.game.mode == "SUSTENTAVEL":
                    price = self.game.get_item_price(item)
                    if self.game.money < price:
                        self.lbl_info.config(text=f"⚠️ Dinheiro insuficiente! ({item} custa ${price})", fg="#BF616A")
                        return
                    self.game.money -= price
                    self.lbl_money.config(text=f"Orçamento: ${self.game.money}")

                if item == "Solar":
                    self.game.nodes.append(Generator(x, y, f"Sol {len(self.game.nodes)+1}", 15, "SOLAR"))
                elif item == "Eólico":
                    self.game.nodes.append(Generator(x, y, f"Eol {len(self.game.nodes)+1}", 20, "EOLICA"))
                elif item == "Carvão":
                    self.game.nodes.append(Generator(x, y, f"Termo-C {len(self.game.nodes)+1}", 35, "CARVAO"))
                elif item == "Termelétrica":
                    self.game.nodes.append(Generator(x, y, f"Termo {len(self.game.nodes)+1}", 50, "TERMELETRICA"))
                elif item == "Nuclear":
                    self.game.nodes.append(Generator(x, y, f"Nuc {len(self.game.nodes)+1}", 150, "NUCLEAR"))
                elif item == "Hidrelétrica":
                    self.game.nodes.append(Generator(x, y, f"Hidro {len(self.game.nodes)+1}", 60, "HIDRELETRICA"))
                elif item == "Bateria":
                    self.game.nodes.append(BatteryNode(x, y, f"Bat {len(self.game.nodes)+1}"))
                elif item == "Subestação":
                    self.game.nodes.append(Substation(x, y, f"Sub {len(self.game.nodes)+1}"))
                elif item == "Transformador":
                    self.game.nodes.append(Node(x, y, f"Trf {len(self.game.nodes)+1}", "subestacao")) 
                elif item == "Cid. Pequena":
                    self.game.nodes.append(City(x, y, f"Cid P {len(self.game.nodes)+1}", 10))
                elif item == "Cid. Grande":
                    self.game.nodes.append(City(x, y, f"Cid G {len(self.game.nodes)+1}", 30))
                elif item == "Poste":
                    self.game.nodes.append(Poste(x, y, f"Pte {len(self.game.nodes)+1}"))
                
                # Record cost for refund
                if self.game.mode == "SUSTENTAVEL":
                    self.game.nodes[-1].cost_paid = price
                self.draw_grid()
                return

        # Linking Items
        clicked_node = self.get_node_at(x, y)
        
        if clicked_node:
            if self.selected_node == None:
                self.selected_node = clicked_node
                self.draw_grid()
            elif self.selected_node == clicked_node:
                self.selected_node = None
                self.draw_grid()
            else:
                exists = any((e.n1 == self.selected_node and e.n2 == clicked_node) or 
                             (e.n1 == clicked_node and e.n2 == self.selected_node) 
                             for e in self.game.edges)
                if not exists:
                    # Define edge capacity and type
                    cap = 5
                    c_type = "ALUMINIO" # Default
                    
                    if self.game.mode in ["CRIATIVO", "SUSTENTAVEL"]:
                        item = self.game.creative_item
                        if item == "Cabo Média":
                            cap, c_type = 15, "MEDIA"
                        elif item == "Cabo Alta":
                            cap, c_type = 40, "ALTA"
                        elif item == "Supercondutor":
                            cap, c_type = 100, "SUPER"
                        else: # Cabo Baixa
                            item = "Cabo Baixa"
                            cap, c_type = 5, "ALUMINIO"
                            
                        # Economy Check for Cables
                        if self.game.mode == "SUSTENTAVEL":
                            price = self.game.get_item_price(item)
                            if self.game.money < price:
                                self.lbl_info.config(text=f"⚠️ Dinheiro insuficiente! ({item} custa ${price})", fg="#BF616A")
                                return
                            self.game.money -= price
                            self.lbl_money.config(text=f"Orçamento: ${self.game.money}")
                    elif self.game.difficulty == "Fácil":
                        cap = 8
                        c_type = "ALUMINIO"
                        
                    new_edge = Edge(self.selected_node, clicked_node, cap, c_type)
                    if self.game.mode == "SUSTENTAVEL":
                        new_edge.cost_paid = price
                    self.game.edges.append(new_edge)
                    self.game.update_flow()
                    self.selected_node = None
                    self.draw_grid()
        else:
            self.selected_node = None
            self.lbl_info.config(text="Info: Planeje a rede")
            self.draw_grid()

    def on_right_click(self, event):
        x, y = event.x, event.y
        edge = self.get_edge_at(x, y)
        if edge:
            # Refund logic for sustainable mode
            if self.game.mode == "SUSTENTAVEL":
                self.game.money += edge.cost_paid
                if self.lbl_money: self.lbl_money.config(text=f"Orçamento: ${self.game.money}")
                
            self.game.edges.remove(edge)
            self.game.update_flow()
            self.lbl_info.config(text="Item removido e valor reembolsado." if self.game.mode == "SUSTENTAVEL" else "Cabo removido.")
            self.draw_grid()
        else: # If no edge, try to remove a node in creative/sustainable mode
            if self.game.mode in ["CRIATIVO", "SUSTENTAVEL"]:
                node = self.get_node_at(event.x, event.y)
                if node:
                    # Refund logic for sustainable mode
                    if self.game.mode == "SUSTENTAVEL":
                        self.game.money += node.cost_paid
                        if self.lbl_money: self.lbl_money.config(text=f"Orçamento: ${self.game.money}")
                    
                    self.game.nodes.remove(node)
                    # Also remove connected edges
                    self.game.edges = [e for e in self.game.edges if e.n1 != node and e.n2 != node]
                    self.game.update_flow()
                    self.lbl_info.config(text=f"{node.name} removido.")
                    self.draw_grid()


    def draw_grid(self):
        self.canvas.delete("all")
        
        canvas_h = self.canvas.winfo_height()
        canvas_w = self.canvas.winfo_width()
        
        # World Stats Display (Top-mid) - Hide in EDUCACIONAL
        if canvas_w > 0 and self.game.mode != "EDUCACIONAL":
            w = self.game.world
            t_str = "☀️ DIA" if 0.2 < w.time < 0.7 else "🌙 NOITE"
            self.canvas.create_text(canvas_w/2, 85, text=f"MUNDO: {t_str} | Vento: {int(w.wind*100)}% | Água: {int(w.water*100)}%", 
                                    fill="#D8DEE9", font=("Arial", 10, "bold"))

        # Draw Edges
        for e in self.game.edges:
            width = 2
            if e.cable_type == "MEDIA": width = 4
            elif e.cable_type == "ALTA": width = 6
            elif e.cable_type == "SUPER": width = 8
            
            dash = ()
            if e.failed:
                color = "#BF616A"
                dash = (5, 5)
            elif self.game.power_on:
                if e.carga_atual > e.capacidade_maxima:
                    # Flashing effect for overloaded cables
                    color = "#BF616A" if self.flash_state else "#4C566A"
                    if not self.flash_state: width = max(1, width - 1)
                elif e.carga_atual > e.capacidade_maxima * 0.9:
                    color = "#EBCB8B"
                else:
                    color = "#A3BE8C"
            else:
                color = "#4C566A"
            
            self.canvas.create_line(e.n1.x, e.n1.y, e.n2.x, e.n2.y, fill=color, width=width, dash=dash)
            
            # Draw load info
            mx = (e.n1.x + e.n2.x) / 2
            my = (e.n1.y + e.n2.y) / 2
            cap_text = f"{e.carga_atual}/{e.capacidade_maxima}"
            self.canvas.create_rectangle(mx-35, my-15, mx+35, my+10, fill="#3B4252", outline="#4C566A")
            self.canvas.create_text(mx, my-2, text=cap_text, fill=color, font=("Arial", 9, "bold"))

        # Draw Nodes
        for n in self.game.nodes:
            if n.type == "gerador":
                node_color = n.color
                self.canvas.create_rectangle(n.x-35, n.y-35, n.x+35, n.y+35, fill="#3B4252", outline=n.color, width=3)
                label = "GEN"
                if n.gen_type == "SOLAR": label = "☀️"
                elif n.gen_type == "EOLICA": label = "🌬️"
                elif n.gen_type == "CARVAO": label = "🏭"
                elif n.gen_type == "TERMELETRICA": label = "🔥"
                elif n.gen_type == "NUCLEAR": label = "⚛️"
                elif n.gen_type == "HIDRELETRICA": label = "💧"
                
                self.canvas.create_text(n.x, n.y-10, text=label, fill="#ECEFF4", font=("Arial", 16, "bold"))
                # Current/Capacity Display (Dynamic)
                cap = getattr(n, 'capacidade_atual', n.capacidade_maxima)
                self.canvas.create_text(n.x, n.y+15, text=f"{n.energy_atual}/{int(cap)} ⚡", fill="#ECEFF4", font=("Arial", 9, "bold"))
                self.canvas.create_text(n.x, n.y-45, text=n.name, fill="#ECEFF4", font=("Arial", 10, "bold"))
            elif n.type == "bateria":
                self.canvas.create_rectangle(n.x-25, n.y-20, n.x+25, n.y+20, fill="#3B4252", outline="#A3BE8C", width=3)
                self.canvas.create_text(n.x, n.y, text=f"🔋 {n.stored_energy}%", fill="#A3BE8C", font=("Arial", 10, "bold"))
                self.canvas.create_text(n.x, n.y-40, text=n.name, fill="#ECEFF4", font=("Arial", 9, "bold"))
            elif n.type == "subestacao":
                self.canvas.create_oval(n.x-30, n.y-30, n.x+30, n.y+30, fill="#3B4252", outline="#88C0D0", width=3)
                self.canvas.create_text(n.x, n.y, text="SUB", fill="#ECEFF4", font=("Arial", 10, "bold"))
                self.canvas.create_text(n.x, n.y-45, text=n.name, fill="#ECEFF4", font=("Arial", 10, "bold"))
            elif n.type == "poste":
                self.canvas.create_line(n.x, n.y-15, n.x, n.y+15, fill="#D8DEE9", width=3)
                self.canvas.create_line(n.x-10, n.y-10, n.x+10, n.y-10, fill="#D8DEE9", width=3)
                self.canvas.create_text(n.x, n.y-25, text="🪵", font=("Arial", 14))
                self.canvas.create_text(n.x, n.y+25, text=n.name, fill="#D8DEE9", font=("Arial", 9))
            elif n.type == "cidade":
                node_color = n.color
                self.canvas.create_polygon(n.x, n.y-40, n.x+35, n.y, n.x+25, n.y+30, n.x-25, n.y+30, n.x-35, n.y, fill="#3B4252", outline=node_color, width=3)
                self.canvas.create_text(n.x, n.y, text=f"{n.energy_atual}/{n.demanda} ⚡", fill="#ECEFF4", font=("Arial", 10, "bold"))
                self.canvas.create_text(n.x, n.y-50, text=n.name, fill="#ECEFF4", font=("Arial", 10, "bold"))
        
        # Draw selection highlight
        if self.selected_node:
            r = self.selected_node.radius + 8
            self.canvas.create_oval(self.selected_node.x-r, self.selected_node.y-r, 
                                    self.selected_node.x+r, self.selected_node.y+r, 
                                    outline="#88C0D0", width=3, dash=(6,6))

        self.draw_legend()

        
    def draw_legend(self):
        # Dynamic positioning based on current canvas size
        canvas_h = self.canvas.winfo_height()
        canvas_w = self.canvas.winfo_width()
        
        if canvas_h < 100 or canvas_w < 100: return # Skip if too small (during initialization)
        
        # Legend (Bottom Left)
        lx1, ly1 = 20, canvas_h - 180
        lx2, ly2 = 300, canvas_h - 20
        self.canvas.create_rectangle(lx1, ly1, lx2, ly2, fill="#3B4252", outline="#4C566A")
        
        self.canvas.create_text(lx1+140, ly1+15, text="📖 LEGENDA DIDÁTICA", fill="#EBCB8B", font=("Arial", 11, "bold"))
        
        items = [
            ("Gerador (Produz ⚡ )", "#D08770", "rect"),
            ("Subestação (Distribui)", "#88C0D0", "oval"),
            ("Cidade (Consome ⚡ )", "#81A1C1", "poly"),
            ("Cabo OK", "#A3BE8C", "line"),
            ("Sobrecarga!", "#BF616A", "line")
        ]
        
        for i, (text, color, shape) in enumerate(items):
            py = ly1 + 45 + (i * 25)
            if shape == "rect":
                self.canvas.create_rectangle(lx1+10, py-7, lx1+25, py+7, fill=color, outline="#ECEFF4")
            elif shape == "oval":
                self.canvas.create_oval(lx1+10, py-10, lx1+30, py+10, outline=color, width=2)
                self.canvas.create_text(lx1+20, py, text="SUB", fill="#ECEFF4", font=("Arial", 6, "bold"))
            elif shape == "poly":
                # Matches the Pentagon shape of Cidade
                cx, cy = lx1+20, py
                self.canvas.create_polygon(cx, cy-10, cx+9, cy-1, cx+6, cy+8, cx-6, cy+8, cx-9, cy-1, fill="#3B4252", outline=color, width=2)
            elif shape == "line":
                self.canvas.create_line(lx1+10, py, lx1+25, py, fill=color, width=3)
            
            self.canvas.create_text(lx1+35, py, text=text, fill="#D8DEE9", font=("Arial", 10), anchor=tk.W)

        # Controls (Bottom Right)
        ctrl_text = "CONTROLES DA AULA:\n• Botão Esquerdo: Ligar nós (ou colocar item)\n• Botão Direito: Remover fio ou nó"
        self.canvas.create_text(canvas_w - 20, canvas_h - 20, text=ctrl_text, fill="#88C0D0", font=("Arial", 11, "bold"), anchor=tk.SE, justify=tk.RIGHT)

        # State overlay (Drawn last to be on top)
        if self.game.state == "WIN" and not self.victory_shown:
            self.victory_shown = True
            self.show_victory_overlay()
        elif self.game.state == "BOSS_BLACKOUT":
            # Darken the background slightly for better readability
            self.canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#2E3440", stipple="gray50")
            self.canvas.create_text(canvas_w/2, 120, text="APAGÃO GERAL!", fill="#BF616A", font=("Arial", 42, "bold"))
            self.canvas.create_text(canvas_w/2, 180, text="O sistema colapsou devido à sobrecarga em cascata.", fill="#ECEFF4", font=("Arial", 18, "bold"))
            self.canvas.create_text(canvas_w/2, 230, text="Clique em 'Reset Nível' no topo para tentar uma nova estratégia.", fill="#D8DEE9", font=("Arial", 14))

    def show_victory_overlay(self):
        overlay = tk.Frame(self.current_frame, bg="#3B4252", bd=5, relief="raised")
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=600, height=400)
        
        tk.Label(overlay, text=f"🏆 FASE {self.game.current_level} CONCLUÍDA!", bg="#3B4252", fg="#A3BE8C", font=("Arial", 24, "bold")).pack(pady=20)
        
        msg_frame = tk.Frame(overlay, bg="#2E3440", padx=20, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        explanation = self.game.get_victory_message()
        tk.Label(msg_frame, text="O que você aprendeu:", bg="#2E3440", fg="#EBCB8B", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        tk.Label(msg_frame, text=explanation, bg="#2E3440", fg="#ECEFF4", font=("Arial", 14), wraplength=520, justify=tk.LEFT).pack(pady=10)
        
        if self.game.current_level < 10:
            btn_next = tk.Button(overlay, text="PRÓXIMA FASE ➔", command=lambda: [overlay.destroy(), self.next_level()], bg="#A3BE8C", fg="#2E3440", font=("Arial", 16, "bold"), padx=20, pady=10, cursor="hand2")
            btn_next.pack(pady=20)
        else:
            tk.Label(overlay, text="🏆 VOCÊ COMPLETOU O MODO! 🏆", bg="#3B4252", fg="#EBCB8B", font=("Arial", 16, "bold")).pack(pady=20)
            tk.Button(overlay, text="VOLTAR AO MENU", command=self.show_menu, bg="#4C566A", fg="#ECEFF4", font=("Arial", 14, "bold")).pack(pady=10)

    def show_help_overlay(self):
        overlay = tk.Frame(self.current_frame, bg="#3B4252", bd=5, relief="raised")
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=800, height=600)
        
        if self.game.mode == "SUSTENTAVEL":
            tut_title = "🍃 Simulação Sustentável 🌍"
            tut_text = (
                "• ÍNDICE DE SUSTENTABILIDADE:\n"
                "  Seu objetivo é mantê-lo acima de 70%. Use fontes renováveis!\n"
                "  Fontes fósseis (Carvão/Gás) geram muita energia, mas poluem.\n\n"
                "• VARIÁVEIS DO AMBIENTE:\n"
                "  ☀️ Solar: Gera energia baseado no sol (Para de funcionar à noite!)\n"
                "  🌬️ Wind: Depende da velocidade do vento no mapa.\n"
                "  💧 Hidro: Estável, mas depende do nível de água dos rios.\n\n"
                "• GESTÃO DE REDE:\n"
                "  Use BATERIAS para guardar energia solar durante o dia e usar à noite!\n"
                "  Cuidado com a Usina Nuclear: se explodir devido à sobrecarga, o nível termina."
            )
        else:
            tut_title = "📚 Guia Pedagógico: Modo Educativo ⚡"
            tut_text = (
                "• CORES DOS CABOS:\n"
                "  Verde: Normal | Amarelo: Cerca do Limite | Vermelho: SOBRECARGA!\n\n"
                "• COMO DIVIDIR CARGA:\n"
                "  Se uma cidade pede 9 MW e o limite é 8 MW, você deve levar\n"
                "  energia por DOIS cabos diferentes vindo de subestações distintas.\n"
                "  Isso evita que um único cabo seja forçado além de sua capacidade técnica.\n\n"
                "• ESTADO 'ROMPEU!':\n"
                "  No modo Médio/Difícil, sobrecarga quebra o fio. Use Botão Direito para remover.\n\n"
                "• DICA DE ENGENHARIA:\n"
                "  Construa todo o seu grid primeiro e só clique em 'Ligar Rede' no final!\n"
                "  Se algo explodir, desligue a rede, ajuste os cabos e ligue de novo."
            )
        
        tk.Label(overlay, text=tut_title, bg="#3B4252", fg="#EBCB8B", font=("Arial", 22, "bold")).pack(pady=15)
        
        txt_frame = tk.Frame(overlay, bg="#2E3440", padx=30, pady=20)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(txt_frame, text=tut_text, bg="#2E3440", fg="#ECEFF4", font=("Arial", 13), justify=tk.LEFT, wraplength=740, anchor="w").pack(fill=tk.BOTH, expand=True)
        
        tk.Button(overlay, text="Fechar Guia", command=overlay.destroy, bg="#BF616A", fg="#ECEFF4", font=("Arial", 14, "bold"), padx=20, cursor="hand2").pack(pady=15)

    def select_creative_item(self, item_name):
        self.game.creative_item = item_name
        self.selected_node = None # Clear current linking selection
        
        # Highlight in item frame
        if hasattr(self, 'item_buttons'):
            for name, btn in self.item_buttons.items():
                if name == item_name:
                    btn.config(bg="#88C0D0", fg="#2E3440")
                else:
                    btn.config(bg="#434C5E", fg="#ECEFF4")

    def flash_loop(self):
        self.flash_state = not self.flash_state
        
        # FINAL BOSS: AI Sabotage Logic
        if self.game.mode == "EDUCACIONAL" and self.game.difficulty == "Difícil" and self.game.current_level == 10 and self.game.power_on and self.game.state == "RUNNING":
            self.sabotage_timer -= 1
            if self.sabotage_timer <= 0:
                self.ai_sabotage()
                self.sabotage_timer = 20 # Reset timer
        
        # Redraw only if there are overloads or active sabotage
        if any(e.carga_atual > e.capacidade_maxima for e in self.game.edges if self.game.power_on) or (self.game.difficulty == "Difícil" and self.game.current_level == 10):
            self.draw_grid()
        self.after(500, self.flash_loop)

    def show_boss_intro(self):
        overlay = tk.Frame(self.current_frame, bg="#3B4252", bd=5, relief="raised")
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=700, height=500)
        
        tk.Label(overlay, text="⚡ BOSS 1: SOBRECARGA SIMPLES ⚡", bg="#3B4252", fg="#BF616A", font=("Arial", 24, "bold")).pack(pady=20)
        
        msg_frame = tk.Frame(overlay, bg="#2E3440", padx=30, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tut_text = (
            "⚠️ ATENÇÃO, ENGENHEIRO! ⚠️\n\n"
            "Nesta fase final do Modo Fácil, você enfrentará um desafio inédito:\n"
            "OS CABOS TÊM UM LIMITE DE CARGA!\n\n"
            "• Se um cabo receber energia demais, ele começará a PISCAR em vermelho.\n"
            "• Se a sobrecarga persistir, o cabo irá se ROMPER e a cidade ficará no escuro.\n"
            "• Para resolver, crie CAMINHOS ALTERNATIVOS para dividir o fluxo de energia.\n\n"
            "Boa sorte na sua primeira grande prova de carga!"
        )
        
        tk.Label(msg_frame, text=tut_text, bg="#2E3440", fg="#ECEFF4", font=("Arial", 14), justify=tk.LEFT, wraplength=640).pack(fill=tk.BOTH, expand=True)
        
        tk.Button(overlay, text="ACEITAR DESAFIO", command=overlay.destroy, bg="#A3BE8C", fg="#2E3440", font=("Arial", 16, "bold"), padx=20, pady=10, cursor="hand2").pack(pady=20)

    def show_boss3_intro(self):
        overlay = tk.Frame(self.current_frame, bg="#3B4252", bd=5, relief="raised")
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=700, height=520)
        
        tk.Label(overlay, text="🔄 BOSS 3: FLUXO CAÓTICO 🔄", bg="#3B4252", fg="#88C0D0", font=("Arial", 24, "bold")).pack(pady=20)
        
        msg_frame = tk.Frame(overlay, bg="#2E3440", padx=30, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tut_text = (
            "🌪️ DESAFIO DE OTIMIZAÇÃO! 🌪️\n\n"
            "Nesta prova final do Modo Médio, a rede está instável:\n"
            "HÁ PERDA DE ENERGIA EM CAMINHOS LONGOS!\n\n"
            "• Se a energia percorrer muitos caminhos (mais de 3 cabos),\n"
            "  ela começará a se dissipar e poderá NÃO chegar à cidade.\n"
            "• Caminhos mais curtos e diretos são essenciais para a vitória.\n"
            "• Use as Subestações com sabedoria para aproximar as rotas.\n\n"
            "Reorganize o grid para garantir que cada ⚡ seja aproveitado!"
        )
        
        tk.Label(msg_frame, text=tut_text, bg="#2E3440", fg="#ECEFF4", font=("Arial", 14), justify=tk.LEFT, wraplength=640).pack(fill=tk.BOTH, expand=True)
        
        tk.Button(overlay, text="ESTRUTURAR GRID", command=overlay.destroy, bg="#88C0D0", fg="#2E3440", font=("Arial", 16, "bold"), padx=20, pady=10, cursor="hand2").pack(pady=20)

    def show_boss6_intro(self):
        overlay = tk.Frame(self.current_frame, bg="#3B4252", bd=5, relief="raised")
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=720, height=550)
        
        tk.Label(overlay, text="🤖 BOSS 6: IA DA REDE (BOSS FINAL) ⚡", bg="#3B4252", fg="#EBCB8B", font=("Arial", 24, "bold")).pack(pady=20)
        
        msg_frame = tk.Frame(overlay, bg="#2E3440", padx=30, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tut_text = (
            "🌐 O SISTEMA GANHOU VIDA! 🌐\n\n"
            "Você chegou ao desafio final. A IA Central está tentando retomar o controle:\n"
            "ELA VAI SABOTAR SUAS CONEXÕES CONSTANTEMENTE!\n\n"
            "• A cada poucos segundos, a IA hackeará um cabo aleatório e o DESLIGARÁ.\n"
            "• Uma rede com caminho único colapsará instantaneamente no Modo Difícil.\n"
            "• A única saída é a REDUNDÂNCIA: crie caminhos extras de segurança\n"
            "  para que a energia flua mesmo quando um cabo for cortado.\n\n"
            "Prove que a inteligência humana supera o algoritmo. Estabilize a rede!"
        )
        
        tk.Label(msg_frame, text=tut_text, bg="#2E3440", fg="#ECEFF4", font=("Arial", 14), justify=tk.LEFT, wraplength=660).pack(fill=tk.BOTH, expand=True)
        
        tk.Button(overlay, text="INICIAR PROTOCOLO DE DEFESA", command=overlay.destroy, bg="#EBCB8B", fg="#2E3440", font=("Arial", 16, "bold"), padx=20, pady=10, cursor="hand2").pack(pady=20)

    def ai_sabotage(self):
        # AI sabotages an active, non-failed edge
        active_edges = [e for e in self.edges if not e.failed]
        if active_edges:
            e = random.choice(active_edges)
            e.failed = True
            self.game.update_flow()
            self.lbl_info.config(text=f"⚠️ ALERTA: IA Sabotou uma Conexão! ⚠️", fg="#BF616A")
            self.draw_grid()

if __name__ == "__main__":
    app = App()
    app.mainloop()
