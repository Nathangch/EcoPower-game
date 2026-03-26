# -*- coding: utf-8 -*-
import pygame
import math
import random
import collections
import asyncio
import time

# --- Constants ---
COLORS = {
    "bg": (46, 52, 64),
    "bg_dark": (36, 41, 51),
    "fg": (236, 239, 244),
    "green": (163, 190, 140),
    "red": (191, 97, 106),
    "yellow": (235, 203, 139),
    "blue": (136, 192, 208),
    "dark_blue": (94, 129, 172),
    "orange": (208, 135, 112),
    "grey": (76, 86, 106),
    "light_grey": (216, 222, 233),
}

# --- Logic Classes (Ported from game.py) ---

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

class Generator(Node):
    def __init__(self, x, y, name, capacity, gen_type="PADRAO"):
        super().__init__(x, y, name, "gerador", capacity)
        self.gen_type = gen_type # TERMELETRICA, HIDRELETRICA, SOLAR, EOLICA, NUCLEAR
        self.thermal_risk = 0 
        self.update_stats()

    def update_stats(self):
        if self.gen_type == "SOLAR": self.color = COLORS["yellow"]
        elif self.gen_type == "EOLICA": self.color = COLORS["blue"]
        elif self.gen_type == "HIDRELETRICA": self.color = COLORS["dark_blue"]
        elif self.gen_type == "TERMELETRICA": self.color = COLORS["grey"]
        elif self.gen_type == "NUCLEAR": self.color = COLORS["red"]
        else: self.color = COLORS["orange"]

class BatteryNode(Node):
    def __init__(self, x, y, name, max_storage=100):
        super().__init__(x, y, name, "bateria", 20) 
        self.max_storage = max_storage
        self.stored_energy = 0
        self.color = COLORS["green"]
        self.charging = False

class Substation(Node):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "subestacao", 0)
        self.radius = 30
        self.color = COLORS["blue"]

class City(Node):
    def __init__(self, x, y, name, demand):
        super().__init__(x, y, name, "cidade", 0)
        self.demanda = demand
        self.radius = 45
        self.color = (129, 161, 193) # #81A1C1

class Poste(Node):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "poste")
        self.color = (129, 161, 193)

class Edge:
    def __init__(self, node1, node2, max_cap, cable_type="ALUMINIO"):
        self.n1 = node1
        self.n2 = node2
        self.capacidade_maxima = max_cap
        self.carga_atual = 0
        self.failed = False
        self.cable_type = cable_type 
        
    def get_other(self, node):
        return self.n2 if self.n1 == node else self.n1

class GameState:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.world = WorldState()
        self.difficulty = "Normal"  # Fácil, Médio, Difícil
        self.state = "RUNNING" 
        self.power_on = False
        self.current_level = 1
        self.mode = "EDUCACIONAL" # Modes: EDUCACIONAL, SUSTENTAVEL, CRIATIVO
        self.creative_item = "Cabo Alumínio"
        
    def build_initial_level(self):
        self.nodes.clear()
        self.edges.clear()
        self.state = "RUNNING"
        self.power_on = False
        
        if self.mode == "CRIATIVO":
            return
        
        diff = self.difficulty
        lvl = self.current_level
        
        if diff == "Fácil":
            num_g = 1 + (lvl // 6)
            num_s = 2 + (lvl // 4)
            num_c = 1 + (lvl // 5)
        elif diff == "Normal" or diff == "Médio":
            num_g = 2 + (lvl // 6)
            num_s = 2 + (lvl // 3)
            num_c = 2 + (lvl // 4)
        else: # Difícil
            num_g = 2 + (lvl // 5)
            num_s = 3 + (lvl // 3)
            num_c = 3 + (lvl // 4)
            
        gen_types = ["PADRAO"] * num_g
        if self.mode == "SUSTENTAVEL":
            types_pool = ["SOLAR", "EOLICA", "HIDRELETRICA", "TERMELETRICA"]
            gen_types = [random.choice(types_pool) for _ in range(num_g)]
            
        gens = [12 + random.randint(0, 8) for _ in range(num_g)] 
        cities = [8 + random.randint(0, 12) for _ in range(num_c)] 
        
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

    def update_flow(self):
        if not self.power_on:
            for n in self.nodes: n.energy_atual = 0
            for e in self.edges: e.carga_atual = 0
            return

        if self.mode != "EDUCACIONAL":
            self.world.update()
        
        for n in self.nodes:
            if n.type == "gerador":
                base = n.capacidade_maxima
                if n.gen_type == "SOLAR" and self.mode != "EDUCACIONAL":
                    mult = max(0, math.sin((self.world.time - 0.25) * 2 * math.pi))
                    n.capacidade_atual = base * mult
                elif n.gen_type == "EOLICA" and self.mode != "EDUCACIONAL":
                    n.capacidade_atual = base * self.world.wind
                elif n.gen_type == "HIDRELETRICA" and self.mode != "EDUCACIONAL":
                    n.capacidade_atual = base * self.world.water
                else:
                    n.capacidade_atual = base
                n.energy_atual = 0 
            elif n.type == "bateria":
                n.capacidade_atual = min(n.capacidade_maxima, n.stored_energy)
                n.energy_atual = 0
            else:
                n.energy_atual = 0

        loop_safe_guard = 0
        while True:
            self._distribute_energy()
            failed = self._check_failures()
            self._check_boss_condition()
            if not failed or self.state == "BOSS_BLACKOUT":
                break
            loop_safe_guard += 1
            if loop_safe_guard > 50:
                break
                
        self._check_win()

    def _distribute_energy(self):
        for e in self.edges: e.carga_atual = 0
        for n in self.nodes: n.energy_atual = 0
            
        total_gen = sum(getattr(n, 'capacidade_atual', 0) for n in self.nodes if n.type == "gerador")
        total_dem = sum(n.demanda for n in self.nodes if n.type == "cidade")
        
        excess = max(0, total_gen - total_dem)
        batteries = [n for n in self.nodes if n.type == "bateria"]
        
        if excess > 0 and batteries and self.mode != "EDUCACIONAL":
            charge_per = excess / len(batteries)
            for b in batteries:
                b.stored_energy = min(b.max_storage, b.stored_energy + charge_per * 0.1) 
                b.charging = True
        else:
            for b in batteries: b.charging = False

        ordered_sources = sorted([n for n in self.nodes if n.type == "gerador" or n.type == "bateria"], 
                                 key=lambda n: getattr(n, 'capacidade_atual', 0), reverse=True)
        
        while True:
            power_moved = False
            for source in ordered_sources:
                cap = getattr(source, 'capacidade_atual', 0)
                if source.energy_atual < cap:
                    path = self.find_path(source, allow_overload=False)
                    if not path:
                        path = self.find_path(source, allow_overload=True)
                        
                    if path:
                        source.energy_atual += 1
                        for edge in path:
                            edge.carga_atual += 1
                            
                        current = source
                        for edge in path:
                            current = edge.get_other(current)
                        current.energy_atual += 1
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
                if not allow_overload and edge.carga_atual >= edge.capacidade_maxima:
                    continue
                nxt = edge.get_other(current)
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [edge]))
        return None

    def _check_failures(self):
        if self.difficulty == "Fácil": return False
        overloaded = [e for e in self.edges if e.carga_atual > e.capacidade_maxima and not e.failed]
        if overloaded:
            if self.difficulty == "Médio" or self.difficulty == "Normal":
                e = overloaded[0]
                e.failed = True
                return True
            elif self.difficulty == "Difícil":
                for e in overloaded: e.failed = True
                return True
        return False
        
    def _check_boss_condition(self):
        if self.state == "BOSS_BLACKOUT" or self.difficulty != "Difícil": return
        total_delivered = sum(c.energy_atual for c in self.nodes if c.type == "cidade")
        total_demand = sum(c.demanda for c in self.nodes if c.type == "cidade")
        if total_demand > 0 and total_delivered == 0 and len([e for e in self.edges if e.failed]) > 2:
            self.state = "BOSS_BLACKOUT"

    def _check_win(self):
        if self.state == "BOSS_BLACKOUT" or self.mode == "CRIATIVO": return
        all_satisfied = all(c.energy_atual >= c.demanda for c in self.nodes if c.type == "cidade")
        no_overloads = all(e.carga_atual <= e.capacidade_maxima for e in self.edges)
        if all_satisfied and no_overloads:
            self.state = "WIN"
        elif self.state == "WIN":
            self.state = "RUNNING" 
            
    def get_sustainability_index(self):
        if self.mode != "SUSTENTAVEL": return 100
        total_gen_capacity = sum(n.capacidade_maxima for n in self.nodes if n.type == "gerador")
        if total_gen_capacity == 0: return 100
        coal_gen_capacity = sum(n.capacidade_maxima for n in self.nodes if n.type == "gerador" and n.gen_type == "TERMELETRICA")
        return 100 - (100 * coal_gen_capacity // total_gen_capacity)

    def get_victory_message(self):
        messages = [
            "Excelente! Você conectou seu primeiro gerador. Em um circuito elétrico básico, a eletricidade sempre percorre o caminho de menor resistência.",
            "Muito bem! Ao usar subestações, você começou a organizar o fluxo. Na engenharia, subestações servem para 'concentrar' e redirecionar a energia.",
            "Ótimo! Você percebeu que geradores podem somar suas forças. É como ligar duas baterias em paralelo.",
            "Incrível! Concluiu a introdução básica. Agora você já sabe que a eletricidade viaja da Fonte para o Consumo.",
            "Atenção Técnica: Aqui você usou circuitos paralelos! Isso reduz acarga nos fios, evitando o superaquecimento.",
            "Redundância: Você criou uma 'Malha em Anel'. No mundo real, isso impede que um bairro fique no escuro por um acidente.",
            "Equilíbrio de Carga: Você distribuiu a energia. Sua estratégia torna o sistema muito mais resiliente e seguro.",
            "Drenagem Térmica: A eletricidade gera calor. Sua rede de várias vias minimiza essa perda energética.",
            "Domínio Urbano: Cidades grandes agora estão seguras! Ao alimentar por múltiplos pontos, você garantiu o suprimento.",
            "Gerenciamento de Pico: Você distribuiu o esforço. Antecipar onde a carga será maior é vital para o sistema.",
            "Arquitetura em Estrela: Usar uma subestação central facilita o monitoramento e permite isolar falhas rapidamente.",
            "Eficiência: Você evitou gargalos. Sua rede minimiza a perda energética e mantém a voltagem estável.",
            "Setorização: Ao separar áreas, você evitou que uma sobrecarga em uma fábrica desligasse o hospital da cidade.",
            "Ponto de Entrega: Metade do caminho! O uso de subestações intermediárias garantiu a qualidade da entrega.",
            "Estabilidade: Sincronizar geração e demanda é o maior desafio do sistema elétrico.",
            "Smart Grids: Antecipar os gargalos e reforçar a malha é o futuro da engenharia elétrica.",
            "Segurança de N-1: O sistema deve continuar operando se UMA conexão falhar. Sua vitória mostrou resiliência.",
            "Engenharia de Sistemas: Parabéns! Você domina todos os conceitos de geração e distribuição elétrica!"
        ]
        if self.current_level <= len(messages):
            return messages[self.current_level - 1]
        return "Parabéns por completar este desafio de engenharia!"

# --- Pygame GUI ---

class Button:
    def __init__(self, x, y, w, h, text, color, hover_color, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action

    def draw(self, screen, font):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text_surf = font.render(self.text, True, COLORS["bg"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

async def main():
    pygame.init()
    screen = pygame.display.set_mode((1100, 820))
    pygame.display.set_caption("EcoPower - Distribuição de Energia")
    clock = pygame.time.Clock()
    font_large = pygame.font.SysFont("Arial", 48, bold=True)
    font_medium = pygame.font.SysFont("Arial", 24, bold=True)
    font_small = pygame.font.SysFont("Arial", 18)
    font_tiny = pygame.font.SysFont("Arial", 12)

    game = GameState()
    ui_state = "MENU" # MENU, MODE_SELECT, DIFF_SELECT, GAME, WIN_MODAL
    selected_node = None

    # UI Buttons for Menu
    menu_buttons = [
        Button(450, 400, 200, 50, "Iniciar Jogo", COLORS["green"], COLORS["blue"], lambda: "MODE_SELECT"),
        Button(450, 470, 200, 50, "Como Jogar", COLORS["yellow"], COLORS["orange"], lambda: "TUTORIAL"),
        Button(450, 540, 200, 50, "Fechar", COLORS["red"], (150, 50, 50), lambda: "QUIT"),
    ]

    mode_buttons = [
        Button(425, 300, 250, 50, "EDUCACIONAL", COLORS["green"], COLORS["blue"], lambda: ("DIFF_SELECT", "EDUCACIONAL")),
        Button(425, 370, 250, 50, "SUSTENTÁVEL", COLORS["blue"], COLORS["dark_blue"], lambda: ("DIFF_SELECT", "SUSTENTAVEL")),
        Button(425, 440, 250, 50, "CRIATIVO", COLORS["yellow"], COLORS["orange"], lambda: ("GAME", "CRIATIVO")),
        Button(425, 550, 250, 50, "Voltar", COLORS["grey"], COLORS["light_grey"], lambda: "MENU"),
    ]

    diff_buttons = [
        Button(425, 300, 250, 50, "FÁCIL", COLORS["green"], COLORS["blue"], lambda: "Fácil"),
        Button(425, 370, 250, 50, "MÉDIO", COLORS["yellow"], COLORS["orange"], lambda: "Médio"),
        Button(425, 440, 250, 50, "DIFÍCIL", COLORS["red"], (150, 50, 50), lambda: "Difícil"),
        Button(425, 550, 250, 50, "Voltar", COLORS["grey"], COLORS["light_grey"], lambda: "MODE_SELECT"),
    ]

    running = True
    while running:
        screen.fill(COLORS["bg"])
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            if ui_state == "MENU":
                for btn in menu_buttons:
                    if btn.is_clicked(event):
                        res = btn.action()
                        if res == "QUIT": running = False
                        else: ui_state = res
            
            elif ui_state == "MODE_SELECT":
                for btn in mode_buttons:
                    if btn.is_clicked(event):
                        res = btn.action()
                        if isinstance(res, tuple):
                            ui_state, mode = res
                            game.mode = mode
                            if mode == "CRIATIVO": game.build_initial_level()
                        else: ui_state = res
            
            elif ui_state == "DIFF_SELECT":
                for btn in diff_buttons:
                    if btn.is_clicked(event):
                        res = btn.action()
                        if res == "MODE_SELECT": ui_state = res
                        else:
                            game.difficulty = res
                            game.build_initial_level()
                            ui_state = "GAME"
            
            elif ui_state == "GAME":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Top bar check
                    if 10 < x < 110 and 10 < y < 50: # Menu button
                        ui_state = "MENU"
                    elif 120 < x < 250 and 10 < y < 50: # Power button
                        game.power_on = not game.power_on
                        game.update_flow()
                    elif 980 < x < 1090 and 10 < y < 50: # Reset button
                        game.build_initial_level()
                        selected_node = None
                    
                    # Canvas Interaction
                    else:
                        node_clicked = None
                        for n in game.nodes:
                            if math.hypot(n.x - x, n.y - y) <= n.radius + 5:
                                node_clicked = n
                                break
                        
                        if event.button == 1: # Left Click
                            if node_clicked:
                                if selected_node is None:
                                    selected_node = node_clicked
                                elif selected_node == node_clicked:
                                    selected_node = None
                                else:
                                    # Create Edge
                                    exists = any((e.n1 == selected_node and e.n2 == node_clicked) or 
                                                 (e.n1 == node_clicked and e.n2 == selected_node) 
                                                 for e in game.edges)
                                    if not exists:
                                        cap = 8 if game.difficulty == "Fácil" else 5
                                        game.edges.append(Edge(selected_node, node_clicked, cap))
                                        game.update_flow()
                                        selected_node = None
                        elif event.button == 3: # Right Click
                            if node_clicked:
                                # Remove edges first
                                game.edges = [e for e in game.edges if e.n1 != node_clicked and e.n2 != node_clicked]
                                if game.mode == "CRIATIVO":
                                    game.nodes.remove(node_clicked)
                                game.update_flow()
                            else:
                                # Check edges
                                for e in game.edges:
                                    # distance formula to line segment simplified
                                    mx, my = (e.n1.x + e.n2.x) / 2, (e.n1.y + e.n2.y) / 2
                                    if math.hypot(x - mx, y - my) < 20:
                                        game.edges.remove(e)
                                        game.update_flow()
                                        break

        # --- Drawing Logic ---
        if ui_state == "MENU":
            title = font_large.render("EcoPower", True, COLORS["yellow"])
            screen.blit(title, (550 - title.get_width()//2, 150))
            for btn in menu_buttons: btn.draw(screen, font_medium)
            
        elif ui_state == "MODE_SELECT":
            title = font_medium.render("Selecione o Modo de Jogo", True, COLORS["yellow"])
            screen.blit(title, (550 - title.get_width()//2, 150))
            for btn in mode_buttons: btn.draw(screen, font_medium)
            
        elif ui_state == "DIFF_SELECT":
            title = font_medium.render("Selecione a Dificuldade", True, COLORS["yellow"])
            screen.blit(title, (550 - title.get_width()//2, 150))
            for btn in diff_buttons: btn.draw(screen, font_medium)
            
        elif ui_state == "GAME":
            # Top Bar
            pygame.draw.rect(screen, COLORS["bg_dark"], (0, 0, 1100, 60))
            # Buttons
            pygame.draw.rect(screen, COLORS["grey"], (10, 10, 100, 40), border_radius=5)
            screen.blit(font_small.render("Menu", True, COLORS["fg"]), (35, 18))
            
            p_color = COLORS["red"] if game.power_on else COLORS["green"]
            p_text = "■ PARAR" if game.power_on else "▶ LIGAR"
            pygame.draw.rect(screen, p_color, (120, 10, 130, 40), border_radius=5)
            screen.blit(font_small.render(p_text, True, COLORS["bg"]), (145, 18))
            
            pygame.draw.rect(screen, COLORS["red"], (980, 10, 110, 40), border_radius=5)
            screen.blit(font_small.render("Reset", True, COLORS["fg"]), (1010, 18))
            
            info_txt = f"Fase: {game.current_level} | {game.mode}"
            screen.blit(font_medium.render(info_txt, True, COLORS["blue"]), (300, 15))

            if game.power_on: game.update_flow()

            # Edges
            for e in game.edges:
                color = COLORS["red"] if e.failed or e.carga_atual > e.capacidade_maxima else COLORS["green"]
                if not game.power_on and not e.failed: color = COLORS["grey"]
                pygame.draw.line(screen, color, (e.n1.x, e.n1.y), (e.n2.x, e.n2.y), 4)
                mx, my = (e.n1.x + e.n2.x) / 2, (e.n1.y + e.n2.y) / 2
                pygame.draw.rect(screen, COLORS["bg_dark"], (mx-25, my-12, 50, 24))
                load_txt = font_tiny.render(f"{e.carga_atual}/{e.capacidade_maxima}", True, color)
                screen.blit(load_txt, (mx-20, my-6))

            # Nodes
            for n in game.nodes:
                if n.type == "gerador":
                    pygame.draw.rect(screen, n.color, (n.x-35, n.y-35, 70, 70), 3)
                    screen.blit(font_tiny.render(n.name, True, COLORS["fg"]), (n.x-30, n.y-50))
                    cap = int(getattr(n, 'capacidade_atual', n.capacidade_maxima))
                    screen.blit(font_small.render(f"{n.energy_atual}/{cap}", True, COLORS["fg"]), (n.x-20, n.y-10))
                elif n.type == "subestacao":
                    pygame.draw.circle(screen, n.color, (n.x, n.y), 30, 3)
                    screen.blit(font_tiny.render("SUB", True, COLORS["fg"]), (n.x-10, n.y-5))
                elif n.type == "cidade":
                    pygame.draw.rect(screen, n.color, (n.x-40, n.y-40, 80, 80), 3)
                    screen.blit(font_small.render(f"{n.energy_atual}/{n.demanda}", True, COLORS["fg"]), (n.x-20, n.y-10))
                
                if selected_node == n:
                    pygame.draw.circle(screen, (255, 255, 255), (n.x, n.y), n.radius+10, 2)

            # Victory/Game Over Overlays
            if game.state == "WIN":
                pygame.draw.rect(screen, (0,0,0,180), (0,0,1100,820))
                vic_msg = font_large.render("FASE CONCLUÍDA!", True, COLORS["green"])
                screen.blit(vic_msg, (550 - vic_msg.get_width()//2, 300))
                btn_next = Button(450, 450, 200, 60, "Próxima Fase", COLORS["green"], COLORS["blue"], None)
                btn_next.draw(screen, font_medium)
                for event in events:
                    if btn_next.is_clicked(event):
                        game.current_level += 1
                        game.build_initial_level()
                        game.state = "RUNNING"
            
            elif game.state == "BOSS_BLACKOUT":
                pygame.draw.rect(screen, (50, 0, 0, 180), (0,0,1100,820))
                msg = font_large.render("APAGÃO GERAL!", True, COLORS["red"])
                screen.blit(msg, (550 - msg.get_width()//2, 300))
                btn_reset = Button(450, 450, 200, 60, "Recomeçar", COLORS["red"], (255,0,0), None)
                btn_reset.draw(screen, font_medium)
                for event in events:
                    if btn_reset.is_clicked(event):
                        game.build_initial_level()

        pygame.display.flip()
        await asyncio.sleep(0) # Required for pygbag
        clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
