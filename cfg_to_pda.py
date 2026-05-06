"""
CFG to PDA Converter - CSCI419 Theory of Computation - Project 02
Pure Python + tkinter (no external libraries).

Algorithm from Tutorial 08:
  Step 1: Push $ to Stack           -> q_start --e,e->$--> q1
  Step 2: Push Start Symbol         -> q1 --e,e->S--> q_loop
  Step 3: Pop/Push Variables        -> q_loop --e,A->rev(body)--> q_loop
  Step 4: Pop/Push Terminals        -> q_loop --a,a->e--> q_loop
  Step 5: Match $ to Accept         -> q_loop --e,$->e--> q_accept
"""
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import math

# ── CFG Parser ───────────────────────────────────────────────────
def parse_cfg(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        raise ValueError("No productions found.")
    variables, terminals, productions = set(), set(), []
    start = None
    for i, line in enumerate(lines, 1):
        if '\u2192' in line:
            parts = line.split('\u2192', 1)
        elif '->' in line:
            parts = line.split('->', 1)
        else:
            raise ValueError(f"Line {i}: Missing arrow (\u2192 or ->).")
        var = parts[0].strip()
        if len(var) != 1 or not var.isupper():
            raise ValueError(f"Line {i}: \"{var}\" must be single uppercase letter.")
        variables.add(var)
        if start is None:
            start = var
        bodies = []
        for alt in parts[1].strip().split('|'):
            alt = alt.strip()
            if not alt:
                raise ValueError(f"Line {i}: Empty alternative.")
            syms = _parse_body(alt, i)
            bodies.append(syms)
            for s in syms:
                if s == '\u03b5': continue
                (variables if s.isupper() else terminals).add(s)
        productions.append({'var': var, 'bodies': bodies})
    return {'variables': variables, 'terminals': terminals,
            'productions': productions, 'start': start}

def _parse_body(t, ln):
    t = t.strip()
    if t in ('\u03b5', 'eps', 'epsilon'):
        return ['\u03b5']
    syms = []
    for ch in t:
        if ch in ' \t': continue
        if ch == '\u03b5':
            if len(t.strip()) == 1: return ['\u03b5']
            raise ValueError(f"Line {ln}: \u03b5 cannot mix with other symbols.")
        if ch.isalnum():
            syms.append(ch)
        else:
            raise ValueError(f"Line {ln}: Unexpected char \"{ch}\".")
    if not syms:
        raise ValueError(f"Line {ln}: Empty body.")
    return syms

# ── CFG to PDA Converter ────────────────────────────────────────
def cfg_to_pda(cfg):
    states = ['q_start', 'q1', 'q_loop', 'q_accept']
    sal = {'\u0024'} | cfg['variables'] | cfg['terminals']
    trans, steps = [], []
    S = cfg['start']
    e = '\u03b5'

    # Step 1
    trans.append(('q_start','q1',e,e,'$','Push $ marker'))
    steps.append((1,'Push $ to Stack',
        'q_start to q1: push bottom-of-stack marker $',
        [f'q_start \u2192 q1 : {e}, {e} \u2192 $']))

    # Step 2
    trans.append(('q1','q_loop',e,e,S,f'Push start symbol {S}'))
    steps.append((2,'Push Start Symbol',
        f'q1 to q_loop: push start symbol {S}',
        [f'q1 \u2192 q_loop : {e}, {e} \u2192 {S}']))

    # Step 3
    s3t = []
    for p in cfg['productions']:
        for body in p['bodies']:
            if body == [e]:
                push = e
            else:
                push = ''.join(reversed(body))
            trans.append(('q_loop','q_loop',e,p['var'],push,
                f"{p['var']} \u2192 {''.join(body)}"))
            s3t.append(f"q_loop \u2192 q_loop : {e}, {p['var']} \u2192 {push}")
    steps.append((3,'Pop/Push Variables (Productions)',
        'For each A \u2192 \u03b1: pop A, push rev(\u03b1)', s3t))

    # Step 4
    s4t = []
    for t in sorted(cfg['terminals']):
        trans.append(('q_loop','q_loop',t,t,e,f'Match terminal {t}'))
        s4t.append(f'q_loop \u2192 q_loop : {t}, {t} \u2192 {e}')
    steps.append((4,'Pop/Push Terminals',
        'For each terminal: read & pop matching terminal', s4t))

    # Step 5
    trans.append(('q_loop','q_accept',e,'$',e,'Accept (pop $)'))
    steps.append((5,'Match $ to Accept',
        'q_loop to q_accept: pop $, stack empty',
        [f'q_loop \u2192 q_accept : {e}, $ \u2192 {e}']))

    return {'states': states, 'sigma': cfg['terminals'],
            'gamma': sal, 'transitions': trans,
            'q0': 'q_start', 'F': ['q_accept'],
            'start_sym': S, 'steps': steps}

# ── PDA Diagram on Canvas ───────────────────────────────────────
class PDADiagram:
    def __init__(self, canvas):
        self.c = canvas
        self.r = 38
        self.positions = {}
        self.c.bind('<Configure>', lambda e: self._on_resize())
        # Colors
        self.BG = '#0d1117'
        self.STATE_FILL = '#161b22'
        self.STATE_EDGE = '#58a6ff'
        self.ACCEPT_EDGE = '#3fb950'
        self.ARROW = '#58a6ff'
        self.LABEL_BG = '#1c2128'
        self.LABEL_FG = '#c9d1d9'
        self.START_CLR = '#f0883e'

    def draw(self, pda):
        self.pda = pda
        self._layout()
        self._render()

    def _on_resize(self):
        if hasattr(self, 'pda'):
            self._layout()
            self._render()

    def _layout(self):
        w = self.c.winfo_width() or 800
        h = self.c.winfo_height() or 400
        cy = h // 2
        spacing = min(180, (w - 140) // 3)
        sx = max(100, (w - spacing * 3) // 2)
        self.positions = {
            'q_start': (sx, cy), 'q1': (sx+spacing, cy),
            'q_loop': (sx+spacing*2, cy), 'q_accept': (sx+spacing*3, cy)}

    def _render(self):
        c = self.c
        c.delete('all')
        c.configure(bg=self.BG)
        r = self.r

        # Group transitions
        groups = {}
        for t in self.pda['transitions']:
            key = (t[0], t[1])
            groups.setdefault(key, []).append(t)

        # Draw edges
        for (src, dst), tlist in groups.items():
            labels = [f"{t[2]}, {t[3]} \u2192 {t[4]}" for t in tlist]
            sx, sy = self.positions[src]
            dx, dy = self.positions[dst]
            if src == dst:
                self._draw_self_loop(sx, sy, labels)
            else:
                self._draw_arrow(sx, sy, dx, dy, labels)

        # Start arrow
        sx, sy = self.positions['q_start']
        x1, x2 = sx - r - 50, sx - r
        c.create_line(x1, sy, x2, sy, fill=self.START_CLR, width=2, arrow=tk.LAST, arrowshape=(10,12,5))
        c.create_text((x1+x2)//2, sy-12, text='start', fill=self.START_CLR,
                       font=('Consolas', 9, 'italic'))

        # Draw states
        for name, (cx, cy) in self.positions.items():
            is_acc = name in self.pda['F']
            edge = self.ACCEPT_EDGE if is_acc else self.STATE_EDGE
            c.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self.STATE_FILL,
                          outline=edge, width=2.5)
            if is_acc:
                c.create_oval(cx-r+5, cy-r+5, cx+r-5, cy+r-5,
                              fill='', outline=self.ACCEPT_EDGE, width=2)
            c.create_text(cx, cy, text=name, fill='#e6edf3',
                          font=('Consolas', 10, 'bold'))

    def _draw_arrow(self, sx, sy, dx, dy, labels):
        c, r = self.c, self.r
        ang = math.atan2(dy-sy, dx-sx)
        x1 = sx + r*math.cos(ang)
        y1 = sy + r*math.sin(ang)
        x2 = dx - r*math.cos(ang)
        y2 = dy - r*math.sin(ang)
        c.create_line(x1, y1, x2, y2, fill=self.ARROW, width=1.8,
                      arrow=tk.LAST, arrowshape=(10,12,5))
        mx, my = (x1+x2)/2, (y1+y2)/2 - 14
        txt = '\n'.join(labels)
        c.create_text(mx, my, text=txt, fill=self.LABEL_FG,
                      font=('Consolas', 8), justify='center', anchor='s')

    def _draw_self_loop(self, cx, cy, labels):
        c, r = self.c, self.r
        # Arc above state
        lx, ly = cx, cy - r - 32
        arc_r = 28
        c.create_arc(cx-arc_r, ly-arc_r, cx+arc_r, ly+arc_r,
                     start=200, extent=140, style='arc',
                     outline=self.ARROW, width=1.8)
        # Small arrowhead
        ax = cx + arc_r * math.cos(math.radians(340))
        ay = ly - arc_r * math.sin(math.radians(340))
        c.create_line(ax-4, ay-6, ax+2, ay+1, fill=self.ARROW, width=1.5)
        c.create_line(ax+6, ay-4, ax+2, ay+1, fill=self.ARROW, width=1.5)
        # Labels
        max_show = 6
        if len(labels) > max_show:
            shown = labels[:max_show-1] + [f'... +{len(labels)-max_show+1} more']
        else:
            shown = labels
        txt = '\n'.join(shown)
        c.create_text(cx, ly - arc_r - 6, text=txt, fill=self.LABEL_FG,
                      font=('Consolas', 7), justify='center', anchor='s')

# ── Main GUI ─────────────────────────────────────────────────────
EXAMPLES = {
    "Example 1": "S \u2192 aTb | b\nT \u2192 Tb | \u03b5",
    "Example 2": "S \u2192 AB\nA \u2192 aAb | \u03b5\nB \u2192 cB | \u03b5",
    "Example 3": "S \u2192 AB\nA \u2192 aA | \u03b5\nB \u2192 bB | \u03b5",
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CFG \u2192 PDA Converter | CSCI419 - Theory of Computation - Project 02")
        self.geometry("1300x800")
        self.minsize(1050, 650)
        self.configure(bg='#0d1117')
        self.option_add('*Font', 'Segoe\\ UI 10')
        self._style()
        self._build()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('.', background='#0d1117', foreground='#c9d1d9',
                     fieldbackground='#161b22', borderwidth=0)
        s.configure('TFrame', background='#0d1117')
        s.configure('Card.TFrame', background='#161b22')
        s.configure('TLabel', background='#0d1117', foreground='#c9d1d9')
        s.configure('Card.TLabel', background='#161b22', foreground='#c9d1d9')
        s.configure('Header.TLabel', background='#0d1117', foreground='#e6edf3',
                     font=('Segoe UI', 16, 'bold'))
        s.configure('Sub.TLabel', background='#0d1117', foreground='#8b949e',
                     font=('Segoe UI', 9))
        s.configure('Section.TLabel', background='#161b22', foreground='#58a6ff',
                     font=('Segoe UI', 11, 'bold'))
        s.configure('Mono.TLabel', background='#161b22', foreground='#e6edf3',
                     font=('Consolas', 10))
        s.configure('Step.TLabel', background='#0d1117', foreground='#d2a8ff',
                     font=('Segoe UI', 10, 'bold'))
        s.configure('Green.TButton', background='#238636', foreground='white',
                     font=('Segoe UI', 11, 'bold'), padding=(12, 6))
        s.map('Green.TButton', background=[('active', '#2ea043')])
        s.configure('Tool.TButton', background='#21262d', foreground='#c9d1d9',
                     font=('Consolas', 11), padding=(6, 2))
        s.map('Tool.TButton', background=[('active', '#30363d')])
        s.configure('Ex.TButton', background='#21262d', foreground='#c9d1d9',
                     font=('Segoe UI', 9), padding=(8, 2))
        s.map('Ex.TButton', background=[('active', '#30363d')])
        s.configure('Badge.TLabel', background='#58a6ff', foreground='#0d1117',
                     font=('Segoe UI', 9, 'bold'), padding=(10, 3))

    def _build(self):
        # Header
        hdr = ttk.Frame(self)
        hdr.pack(fill='x', padx=16, pady=(10, 4))
        ttk.Label(hdr, text='\u2699  CFG \u2192 PDA Converter',
                  style='Header.TLabel').pack(side='left')
        ttk.Label(hdr, text='CSCI419 \u2022 Theory of Computation \u2022 Project 02',
                  style='Sub.TLabel').pack(side='left', padx=12)
        ttk.Label(hdr, text=' Project 02 ', style='Badge.TLabel').pack(side='right')

        # Main panes
        pw = ttk.PanedWindow(self, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=8, pady=4)

        # Left panel
        left = ttk.Frame(pw)
        pw.add(left, weight=2)

        # Input card
        card = ttk.Frame(left, style='Card.TFrame')
        card.pack(fill='x', padx=4, pady=4)
        ttk.Label(card, text='\U0001f4dd  Input CFG', style='Section.TLabel').pack(
            anchor='w', padx=10, pady=(8, 2))
        ttk.Label(card, text='Use \u2192 or -> | Separate with | | \u03b5 or eps for epsilon',
                  style='Card.TLabel', font=('Segoe UI', 8),
                  foreground='#8b949e').pack(anchor='w', padx=10)

        self.cfg_input = tk.Text(card, height=5, bg='#0d1117', fg='#e6edf3',
            insertbackground='#e6edf3', font=('Consolas', 12), relief='flat',
            bd=0, highlightthickness=1, highlightcolor='#30363d',
            highlightbackground='#30363d', wrap='word')
        self.cfg_input.pack(fill='x', padx=10, pady=6)
        self.cfg_input.insert('1.0', 'S \u2192 aTb | b\nT \u2192 Tb | \u03b5')

        # Toolbar
        tb = ttk.Frame(card, style='Card.TFrame')
        tb.pack(fill='x', padx=10, pady=(0, 4))
        for txt, ins in [('\u2192',' \u2192 '),('\u03b5','\u03b5'),('|',' | ')]:
            ttk.Button(tb, text=txt, style='Tool.TButton',
                command=lambda c=ins: self.cfg_input.insert('insert', c)).pack(side='left', padx=2)
        ttk.Label(tb, text='  Examples:', style='Card.TLabel',
                  foreground='#8b949e', font=('Segoe UI', 9)).pack(side='left', padx=(10,4))
        for name, val in EXAMPLES.items():
            ttk.Button(tb, text=name, style='Ex.TButton',
                command=lambda v=val: self._set_ex(v)).pack(side='left', padx=2)

        ttk.Button(card, text='\u25b6  Convert to PDA', style='Green.TButton',
                   command=self._convert).pack(fill='x', padx=10, pady=(4, 10))

        # Scrollable results
        rf = ttk.Frame(left)
        rf.pack(fill='both', expand=True, padx=4, pady=4)
        self.results_canvas = tk.Canvas(rf, bg='#0d1117', highlightthickness=0)
        vsb = ttk.Scrollbar(rf, orient='vertical', command=self.results_canvas.yview)
        self.results_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.results_canvas.pack(side='left', fill='both', expand=True)
        self.results_frame = ttk.Frame(self.results_canvas)
        self.results_canvas.create_window((0,0), window=self.results_frame, anchor='nw')
        self.results_frame.bind('<Configure>',
            lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox('all')))
        self.results_canvas.bind_all('<MouseWheel>',
            lambda e: self.results_canvas.yview_scroll(-1*(e.delta//120), 'units'))

        ttk.Label(self.results_frame, text='Enter a CFG and click Convert.',
                  foreground='#8b949e').pack(anchor='w', padx=8, pady=8)

        # Right panel - diagram
        right = ttk.Frame(pw)
        pw.add(right, weight=3)
        ttk.Label(right, text='\U0001f500  PDA State Diagram',
                  style='Header.TLabel', font=('Segoe UI', 13, 'bold')).pack(
                      anchor='w', padx=12, pady=(8, 4))
        self.diagram_canvas = tk.Canvas(right, bg='#0d1117', highlightthickness=0)
        self.diagram_canvas.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        self.pda_diagram = PDADiagram(self.diagram_canvas)

    def _set_ex(self, val):
        self.cfg_input.delete('1.0', 'end')
        self.cfg_input.insert('1.0', val)

    def _convert(self):
        text = self.cfg_input.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning('Empty', 'Please enter a CFG.')
            return
        try:
            cfg = parse_cfg(text)
            pda = cfg_to_pda(cfg)
        except ValueError as ex:
            messagebox.showerror('Error', str(ex))
            return

        # Clear results
        for w in self.results_frame.winfo_children():
            w.destroy()

        self._show_cfg(cfg)
        self._show_steps(pda)
        self._show_formal(pda)
        self._show_table(pda)
        self.pda_diagram.draw(pda)

    # ── Result sections ──
    def _card(self, title):
        f = ttk.Frame(self.results_frame, style='Card.TFrame')
        f.pack(fill='x', padx=4, pady=4)
        ttk.Label(f, text=title, style='Section.TLabel').pack(anchor='w', padx=10, pady=(8,4))
        return f

    def _show_cfg(self, cfg):
        f = self._card('\U0001f4c4  Parsed CFG')
        for p in cfg['productions']:
            bstr = ' | '.join(''.join(b) for b in p['bodies'])
            ttk.Label(f, text=f"  {p['var']} \u2192 {bstr}", style='Mono.TLabel').pack(
                anchor='w', padx=12, pady=1)
        ttk.Frame(f, height=4, style='Card.TFrame').pack()

    def _show_steps(self, pda):
        f = self._card('\U0001f4cb  Conversion Steps')
        colors = {1:'#f0883e', 2:'#58a6ff', 3:'#d2a8ff', 4:'#3fb950', 5:'#f778ba'}
        for num, title, desc, tlist in pda['steps']:
            sf = ttk.Frame(f)
            sf.pack(fill='x', padx=8, pady=3)
            lbl = ttk.Label(sf, text=f'  Step {num}: {title}',
                font=('Segoe UI', 10, 'bold'), foreground=colors.get(num,'#58a6ff'))
            lbl.pack(anchor='w', padx=6, pady=(4,0))
            ttk.Label(sf, text=f'  {desc}', foreground='#8b949e',
                      font=('Segoe UI', 9), wraplength=360).pack(anchor='w', padx=6)
            for t in tlist[:8]:
                ttk.Label(sf, text=f'    {t}', font=('Consolas', 9),
                          foreground='#c9d1d9').pack(anchor='w', padx=6)
            if len(tlist) > 8:
                ttk.Label(sf, text=f'    ... +{len(tlist)-8} more',
                          foreground='#8b949e', font=('Segoe UI', 9)).pack(anchor='w', padx=6)

    def _show_formal(self, pda):
        f = self._card('\U0001f523  PDA Formal Definition')
        e = '\u03b5'
        items = [
            ('P', '( Q, \u03a3, \u0393, \u03b4, q\u2080, F )'),
            ('Q', '{ ' + ', '.join(pda['states']) + ' }'),
            ('\u03a3', '{ ' + ', '.join(sorted(pda['sigma'])) + ' }'),
            ('\u0393', '{ ' + ', '.join(sorted(pda['gamma'])) + ' }'),
            ('q\u2080', pda['q0']),
            ('F', '{ ' + ', '.join(pda['F']) + ' }'),
        ]
        for lbl, val in items:
            row = ttk.Frame(f, style='Card.TFrame')
            row.pack(fill='x', padx=10, pady=1)
            ttk.Label(row, text=f'  {lbl}  =', style='Card.TLabel',
                      foreground='#d2a8ff', font=('Segoe UI', 11, 'bold'),
                      width=6, anchor='e').pack(side='left')
            ttk.Label(row, text=f'  {val}', style='Mono.TLabel').pack(side='left', padx=4)

    def _show_table(self, pda):
        f = self._card('\U0001f4ca  Transition Table')
        # Header
        hdr = ttk.Frame(f, style='Card.TFrame')
        hdr.pack(fill='x', padx=8, pady=(4,2))
        cols = ['#', 'From', 'Input', 'Pop', 'Push', 'To', 'Description']
        ws = [4, 8, 5, 5, 7, 8, 20]
        for c, w in zip(cols, ws):
            ttk.Label(hdr, text=c, style='Card.TLabel', foreground='#58a6ff',
                      font=('Consolas', 9, 'bold'), width=w).pack(side='left', padx=1)
        # Rows
        for i, t in enumerate(pda['transitions'], 1):
            bg = '#161b22' if i % 2 == 0 else '#0d1117'
            row = tk.Frame(f, bg=bg, height=22)
            row.pack(fill='x', padx=8)
            row.pack_propagate(False)
            vals = [str(i), t[0], t[2], t[3], t[4], t[1], t[5]]
            for v, w in zip(vals, ws):
                tk.Label(row, text=v, bg=bg, fg='#c9d1d9',
                         font=('Consolas', 9), width=w, anchor='w').pack(side='left', padx=1)

if __name__ == '__main__':
    app = App()
    app.mainloop()
